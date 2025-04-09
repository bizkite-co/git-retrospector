# iac/iac/iac_stack.py
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_logs as logs,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_lambda as lambda_,
    aws_ecr_assets as ecr_assets,
    CfnOutput,
    Token,  # Import Token for checking unresolved values
)
import aws_cdk.aws_lambda_python_alpha as lambda_alpha
from constructs import Construct
import os
import re  # Import re for sanitizing bucket name


class RetrospectorInfraStack(Stack):  # Renamed class

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- Git Lambda Layer ---
        git_layer = lambda_.LayerVersion(
            self,
            "GitLayer",
            code=lambda_.Code.from_asset(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "lambda_layers",
                    "git",
                    "git-layer.zip",
                )
            ),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="Layer containing Git binary and dependencies",
        )

        # --- Existing Resources ---

        # Make DynamoDB table name unique to the stack instance
        commit_status_table = dynamodb.Table(
            self,
            "CommitStatusTable",
            table_name=f"GitRetrospectorCommitStatus-{construct_id}",  # Modified name
            partition_key=dynamodb.Attribute(
                name="repo_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="commit_hash", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # Be cautious in production
        )

        # Make S3 bucket name unique and compliant
        # Bucket names must be globally unique, lowercase, no underscores, 3-63 chars.
        # Sanitize construct_id and combine with account/region for better uniqueness.
        sanitized_construct_id = re.sub(r"[^a-z0-9-]", "-", construct_id.lower())
        # Ensure the combined name doesn't exceed 63 chars and follows rules
        base_bucket_name = f"git-retrospector-results-{sanitized_construct_id}"
        # Use unresolved tokens for account/region if available, otherwise handle
        # potential placeholders
        account_part = (
            self.account if not Token.is_unresolved(self.account) else "account"
        )
        region_part = self.region if not Token.is_unresolved(self.region) else "region"
        full_bucket_name = f"{base_bucket_name}-{account_part}-{region_part}"
        # Truncate if necessary, ensuring it doesn't end with a hyphen
        final_bucket_name = full_bucket_name[:63].rstrip("-")

        results_bucket = s3.Bucket(
            self,
            "ResultsBucket",
            bucket_name=final_bucket_name,  # Modified and sanitized name
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,  # Be cautious in production
            auto_delete_objects=True,  # Useful for dev/test
        )

        # --- New Lambda Function (Initiation) ---

        initiation_lambda = lambda_alpha.PythonFunction(
            self,
            "InitiationLambda",
            entry=os.path.join(
                os.path.dirname(__file__), "..", "..", "lambda_fns", "initiation"
            ),
            index="handler.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            timeout=Duration.minutes(5),
            memory_size=1024,
            environment={
                # Pass the dynamically generated table name to the lambda
                "COMMIT_STATUS_TABLE_NAME": commit_status_table.table_name,
                "GIT_EXECUTABLE_PATH": "/opt/bin/git",  # Path provided by the layer
                # Tell git where to find helpers
                "GIT_EXEC_PATH": "/opt/libexec/git-core",
            },
            layers=[git_layer],  # Attach the Git layer
        )

        commit_status_table.grant_write_data(initiation_lambda)

        # --- ECS Resources (Processing Task) ---

        cluster = ecs.Cluster(self, "RetrospectorCluster")

        task_role = iam.Role(
            self,
            "FargateTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Role assumed by ECS Fargate tasks for Git Retrospector",
        )

        commit_status_table.grant_read_write_data(task_role)
        results_bucket.grant_write(task_role)

        # Define Docker Image Asset
        docker_image_asset = ecr_assets.DockerImageAsset(
            self,
            "RetrospectorFargateTaskImage",
            directory=os.path.join(
                os.path.dirname(__file__), "..", "..", "fargate_task"
            ),  # Closing parenthesis for os.path.join
            platform=ecr_assets.Platform.LINUX_AMD64,  # Specify target platform
        )  # Closing parenthesis for DockerImageAsset

        task_definition = ecs.FargateTaskDefinition(
            self,
            "RetrospectorTaskDef",
            task_role=task_role,
            cpu=1024,
            memory_limit_mib=2048,
        )

        # Make log group name unique to the stack instance
        log_group = logs.LogGroup(
            self,
            "RetrospectorTaskLogGroup",
            log_group_name=f"/ecs/GitRetrospectorTask-{construct_id}",  # Modified name
            removal_policy=RemovalPolicy.DESTROY,  # Be cautious in production
        )  # Closing parenthesis for LogGroup

        container = task_definition.add_container(
            "RetrospectorContainer",
            image=ecs.ContainerImage.from_docker_image_asset(docker_image_asset),
            logging=ecs.LogDrivers.aws_logs(
                log_group=log_group,
                stream_prefix="ecs",
            ),
            environment={
                # Pass the dynamically generated table and bucket names
                # These are static for all tasks within the execution
                "DYNAMODB_TABLE_NAME": commit_status_table.table_name,
                "S3_BUCKET_NAME": results_bucket.bucket_name,
            },
        )

        # --- Step Functions State Machine ---

        fargate_task_state = sfn_tasks.EcsRunTask(
            self,
            "ProcessSingleCommitTask",
            integration_pattern=sfn.IntegrationPattern.RUN_JOB,
            cluster=cluster,
            task_definition=task_definition,
            launch_target=sfn_tasks.EcsFargateLaunchTarget(
                platform_version=ecs.FargatePlatformVersion.LATEST
            ),
            # Input for this task comes from the 'parameters' of the Map state.
            container_overrides=[
                sfn_tasks.ContainerOverride(
                    container_definition=container,
                    environment=[
                        # Pass only the variables needed per commit
                        sfn_tasks.TaskEnvironmentVariable(
                            name="REPO_URL",
                            # Reference repo_url from the Map iterator's input
                            value=sfn.JsonPath.string_at("$.repo_url"),
                        ),
                        sfn_tasks.TaskEnvironmentVariable(
                            name="COMMIT_HASH_TO_PROCESS",
                            # Reference commit_hash from the Map iterator's input
                            value=sfn.JsonPath.string_at(
                                "$.commit_details.commit_hash"
                            ),
                        ),
                    ],
                )
            ],
            result_path=sfn.JsonPath.DISCARD,
        )

        map_state = sfn.Map(
            self,
            "ProcessCommitsMap",
            items_path=sfn.JsonPath.string_at("$.commits"),
            # Construct input for each iteration: pass repo_url and current commit item
            parameters={
                "repo_url": sfn.JsonPath.string_at(
                    "$.repo_url"
                ),  # From main state input
                # Embed the current map item value
                "commit_details.$": "$$.Map.Item.Value",
            },
            # The output of 'parameters' becomes the input '$' for
            # the iterator (fargate_task_state)
            max_concurrency=10,
        )
        map_state.iterator(fargate_task_state)

        completion_state = sfn.Pass(
            self, "ProcessingComplete", comment="All commits processed successfully"
        )

        definition = map_state.next(completion_state)

        # Make state machine name unique to the stack instance
        state_machine = sfn.StateMachine(
            self,
            "GitRetrospectorStateMachine",
            # Modified name
            state_machine_name=f"GitRetrospectorStateMachine-{construct_id}",
            definition=definition,
            logs=sfn.LogOptions(
                destination=logs.LogGroup(
                    self,
                    "StateMachineLogGroup",
                    # Modified name
                    log_group_name=f"""/aws/stepfunctions/GitRetrospectorStateMachine-{
                         construct_id
                    }""",
                    removal_policy=RemovalPolicy.DESTROY,  # Be cautious in production
                ),
                level=sfn.LogLevel.ALL,
                include_execution_data=True,
            ),
        )

        # --- Grant Permissions (Post-Definition) ---

        initiation_lambda.add_environment(
            "STATE_MACHINE_ARN", state_machine.state_machine_arn
        )
        # Pass the dynamic bucket name to the initiation lambda if it needs it
        initiation_lambda.add_environment(
            "RESULTS_BUCKET_NAME", results_bucket.bucket_name
        )
        results_bucket.grant_read_write(
            initiation_lambda
        )  # Grant S3 permissions if needed by lambda

        state_machine.grant_start_execution(initiation_lambda)

        # --- Outputs ---
        CfnOutput(self, "CommitStatusTableName", value=commit_status_table.table_name)
        CfnOutput(self, "ResultsBucketName", value=results_bucket.bucket_name)
        CfnOutput(self, "InitiationLambdaArn", value=initiation_lambda.function_arn)
        CfnOutput(self, "ClusterName", value=cluster.cluster_name)
        CfnOutput(self, "TaskDefinitionArn", value=task_definition.task_definition_arn)
        CfnOutput(self, "TaskRoleArn", value=task_role.role_arn)
        CfnOutput(self, "StateMachineArn", value=state_machine.state_machine_arn)
        CfnOutput(self, "DockerImageAssetUri", value=docker_image_asset.image_uri)
        CfnOutput(
            self, "GitLayerArn", value=git_layer.layer_version_arn
        )  # Added output for layer ARN
