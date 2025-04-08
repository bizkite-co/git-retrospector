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
            # environment={
            #     "DYNAMODB_TABLE_NAME": commit_status_table.table_name,
            #     "S3_BUCKET_NAME": results_bucket.bucket_name,
            # }
        )

        # Outputs (optional, but helpful)
        CfnOutput(self, "CommitStatusTableName", value=commit_status_table.table_name)
        CfnOutput(self, "ResultsBucketName", value=results_bucket.bucket_name)
        CfnOutput(self, "ClusterName", value=cluster.cluster_name)
        CfnOutput(self, "TaskDefinitionArn", value=task_definition.task_definition_arn)
        CfnOutput(self, "TaskRoleArn", value=task_role.role_arn)
        CfnOutput(self, "Container", value=container)
