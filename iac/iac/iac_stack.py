from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_ecs as ecs,
    # Although not used directly here, good practice to import if related
    # aws_ecr_assets as ecr_assets,
    aws_iam as iam,
    aws_logs as logs,
    aws_stepfunctions as sfn,  # Added import
    aws_stepfunctions_tasks as sfn_tasks,  # Added import
    CfnOutput,
)
from constructs import Construct


class IacStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- Existing Resources ---

        # Define the DynamoDB table for commit status
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
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Define the S3 bucket for storing results
        results_bucket = s3.Bucket(
            self,
            "ResultsBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # --- New ECS Resources ---

        # Define the ECS Cluster
        # Using default VPC created by CDK
        cluster = ecs.Cluster(self, "RetrospectorCluster")

        # Define the IAM Task Role for Fargate Tasks
        task_role = iam.Role(
            self,
            "FargateTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Role assumed by ECS Fargate tasks for Git Retrospector",
        )

        # Grant permissions to the Task Role
        commit_status_table.grant_read_write_data(task_role)
        results_bucket.grant_write(task_role)
        # Add Secrets Manager permissions if needed later
        # Example: secretsmanager.Secret.from_secret_name_v2(...).grant_read(task_role)

        # Define the Fargate Task Definition
        task_definition = ecs.FargateTaskDefinition(
            self,
            "RetrospectorTaskDef",
            task_role=task_role,
            cpu=1024,  # 1 vCPU
            memory_limit_mib=2048,  # 2 GB RAM
        )

        # Define the Log Group for the container
        log_group = logs.LogGroup(
            self,
            "RetrospectorTaskLogGroup",
            log_group_name="/ecs/GitRetrospectorTask",
            removal_policy=RemovalPolicy.DESTROY,  # Clean up logs in dev
        )

        # Add a container to the Task Definition
        container = task_definition.add_container(
            "RetrospectorContainer",
            # Placeholder image - replace with actual application image later
            image=ecs.ContainerImage.from_registry(
                "public.ecr.aws/amazonlinux/amazonlinux:latest"
            ),
            logging=ecs.LogDrivers.aws_logs(
                log_group=log_group,
                stream_prefix="ecs",  # Prefix for log streams within the group
            ),
            # Environment variables can be added here later
            environment={
                "DYNAMODB_TABLE_NAME": commit_status_table.table_name,
                "S3_BUCKET_NAME": results_bucket.bucket_name,
                # COMMIT_HASH_TO_PROCESS will be added via Step Functions override
            },
        )

        # --- Step Functions State Machine ---

        # Placeholder: Initiation State
        initiation_state = sfn.Pass(
            self,
            "Initiation",
            comment="Placeholder: Fetch repo info and trigger commit list retrieval",
            # Input: { "repo_owner": "...", "repo_name": "...",
            # "selection_criteria": {...} }
        )

        # Placeholder: Get Commit List State
        get_commit_list_state = sfn.Pass(
            self,
            "Get Commit List",
            comment="Placeholder: Fetch commit list based on input",
            # Output: { "commits": [{"hash": "..."}, {"hash": "..."}] }
            # Example output for testing:
            result=sfn.Result.from_object(
                {"commits": [{"hash": "example_hash_1"}, {"hash": "example_hash_2"}]}
            ),
            result_path="$.commit_list_output",  # Place example output somewhere
        )

        # Fargate Task State (to be run inside the Map state)
        fargate_task_state = sfn_tasks.EcsRunTask(
            self,
            "ProcessSingleCommitTask",
            integration_pattern=sfn.IntegrationPattern.RUN_JOB,  # .sync
            cluster=cluster,
            task_definition=task_definition,
            launch_target=sfn_tasks.EcsFargateLaunchTarget(
                # Add the required platform_version
                platform_version=ecs.FargatePlatformVersion.LATEST
            ),
            container_overrides=[
                sfn_tasks.ContainerOverride(
                    container_definition=container,
                    environment=[
                        sfn_tasks.TaskEnvironmentVariable(
                            name="COMMIT_HASH_TO_PROCESS",
                            # Access the 'hash' field from the current item being
                            # processed by the Map state
                            value=sfn.JsonPath.string_at("$$.Map.Item.Value.hash"),
                        )
                    ],
                )
            ],
            # Pass relevant parts of the state to the task if needed, or
            # rely on overrides
            # input_path="$.some_input_for_task"
            result_path=sfn.JsonPath.DISCARD,  # Discard Fargate task output for now
        )

        # Map State to process commits in parallel
        map_state = sfn.Map(
            self,
            "ProcessCommitsMap",
            items_path=sfn.JsonPath.string_at(
                "$.commit_list_output.commits"
            ),  # Use the output from the previous step
            max_concurrency=10,
            # Define the workflow for each item in the list
            # result_path="$.map_results" # Optional: Where to store
            # results of map iterations
        )
        map_state.iterator(fargate_task_state)  # Run the Fargate task for each commit

        # Placeholder: Completion State
        completion_state = sfn.Pass(
            self, "Processing Complete", comment="All commits processed successfully"
        )

        # Define the State Machine Definition by chaining the states
        definition = (
            initiation_state.next(get_commit_list_state)
            .next(map_state)
            .next(completion_state)
        )

        # Create the State Machine
        state_machine = sfn.StateMachine(
            self,
            "GitRetrospectorStateMachine",
            state_machine_name="GitRetrospectorStateMachine",
            definition=definition,
            # Consider adding logging configuration
            # logs=sfn.LogOptions(
            #     destination=logs.LogGroup(self, "StateMachineLogGroup"),
            #     level=sfn.LogLevel.ALL,
            #     include_execution_data=True
            # )
        )

        # --- Outputs ---
        CfnOutput(self, "CommitStatusTableName", value=commit_status_table.table_name)
        CfnOutput(self, "ResultsBucketName", value=results_bucket.bucket_name)
        CfnOutput(self, "ClusterName", value=cluster.cluster_name)
        CfnOutput(self, "TaskDefinitionArn", value=task_definition.task_definition_arn)
        CfnOutput(self, "TaskRoleArn", value=task_role.role_arn)
        # CfnOutput(self, "ContainerName", value=container.container_name)
        # Construct doesn't expose name directly
        CfnOutput(self, "StateMachineArn", value=state_machine.state_machine_arn)
