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
    CfnOutput,
)
import aws_cdk.aws_lambda_python_alpha as lambda_alpha  # Reverted import
from constructs import Construct
import os


class IacStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- Existing Resources ---

        commit_status_table = dynamodb.Table(
            self,
            "CommitStatusTable",
            table_name="GitRetrospectorCommitStatus",
            partition_key=dynamodb.Attribute(
                name="repo_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="commit_hash", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        results_bucket = s3.Bucket(
            self,
            "ResultsBucket",
            bucket_name=f"git-retrospector-results-{self.account}-{self.region}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # --- New Lambda Function (Initiation) ---

        initiation_lambda = lambda_alpha.PythonFunction(  # Reverted usage
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
                "COMMIT_STATUS_TABLE_NAME": commit_status_table.table_name,
                "GIT_EXECUTABLE_PATH": "/opt/bin/git",  # Assuming use of a Git layer
            },
            # layers=[lambda_.LayerVersion.from_layer_version_arn(self,
            # "GitLayer", "arn:aws:lambda:REGION:ACCOUNT_ID:layer:GitLayer:VERSION")]
            # Example if using layer
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

        task_definition = ecs.FargateTaskDefinition(
            self,
            "RetrospectorTaskDef",
            task_role=task_role,
            cpu=1024,
            memory_limit_mib=2048,
        )

        log_group = logs.LogGroup(
            self,
            "RetrospectorTaskLogGroup",
            log_group_name="/ecs/GitRetrospectorTask",
            removal_policy=RemovalPolicy.DESTROY,
        )

        container = task_definition.add_container(
            "RetrospectorContainer",
            image=ecs.ContainerImage.from_registry(
                "public.ecr.aws/amazonlinux/amazonlinux:latest"  # Placeholder
            ),
            logging=ecs.LogDrivers.aws_logs(
                log_group=log_group,
                stream_prefix="ecs",
            ),
            environment={
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
            container_overrides=[
                sfn_tasks.ContainerOverride(
                    container_definition=container,
                    environment=[
                        sfn_tasks.TaskEnvironmentVariable(
                            name="REPO_ID",
                            value=sfn.JsonPath.string_at("$.repo_id"),
                        ),
                        sfn_tasks.TaskEnvironmentVariable(
                            name="COMMIT_HASH_TO_PROCESS",
                            value=sfn.JsonPath.string_at(
                                "$$.Map.Item.Value.commit_hash"
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
            max_concurrency=10,
        )
        map_state.iterator(fargate_task_state)

        completion_state = sfn.Pass(
            self, "ProcessingComplete", comment="All commits processed successfully"
        )

        definition = map_state.next(completion_state)

        state_machine = sfn.StateMachine(
            self,
            "GitRetrospectorStateMachine",
            state_machine_name="GitRetrospectorStateMachine",
            definition=definition,
            logs=sfn.LogOptions(
                destination=logs.LogGroup(
                    self, "StateMachineLogGroup", removal_policy=RemovalPolicy.DESTROY
                ),
                level=sfn.LogLevel.ALL,
                include_execution_data=True,
            ),
        )

        # --- Grant Permissions (Post-Definition) ---

        initiation_lambda.add_environment(
            "STATE_MACHINE_ARN", state_machine.state_machine_arn
        )
        state_machine.grant_start_execution(initiation_lambda)

        # --- Outputs ---
        CfnOutput(self, "CommitStatusTableName", value=commit_status_table.table_name)
        CfnOutput(self, "ResultsBucketName", value=results_bucket.bucket_name)
        CfnOutput(self, "InitiationLambdaArn", value=initiation_lambda.function_arn)
        CfnOutput(self, "ClusterName", value=cluster.cluster_name)
        CfnOutput(self, "TaskDefinitionArn", value=task_definition.task_definition_arn)
        CfnOutput(self, "TaskRoleArn", value=task_role.role_arn)
        CfnOutput(self, "StateMachineArn", value=state_machine.state_machine_arn)
