# Task: Define ECS Cluster and Fargate Task Definition (Phase 3 - Step 1b)

**Objective:** Define the AWS ECS Cluster and Fargate Task Definition using the AWS CDK, building upon the existing CDK stack.

**Context:** This follows the initialization of the CDK project and definition of DynamoDB/S3 resources. It defines the compute environment for running the retrospector tasks in parallel.

**Prerequisites:**
*   CDK project initialized in `iac/`.
*   `iac/iac/iac_stack.py` contains definitions for DynamoDB table and S3 bucket.

**Detailed Steps:**

1.  **Install ECS CDK Libraries:**
    *   Ensure you are in the CDK project directory (`iac/`) with the virtual environment activated.
    *   Install necessary CDK libraries for ECS and IAM: `pip install aws-cdk.aws-ecs aws-cdk.aws-ecr-assets aws-cdk.aws-iam`.
    *   Update `requirements.txt` (or equivalent).

2.  **Define Resources in `iac/iac/iac_stack.py`:**
    *   Import necessary modules (`aws_ecs`, `aws_ecr_assets`, `aws_iam`).
    *   **ECS Cluster:**
        *   Define an `ecs.Cluster` resource. A simple definition is often sufficient initially (e.g., `ecs.Cluster(self, "RetrospectorCluster", vpc=None)` - CDK will create a default VPC if `vpc` is not specified, or you can define/import one).
    *   **IAM Task Role:**
        *   Define an `iam.Role` for the Fargate task.
        *   Set `assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")`.
        *   Attach necessary permissions:
            *   Read/Write access to the `CommitStatusTable` DynamoDB table (use `table.grant_read_write_data(task_role)`).
            *   Write access to the `ResultsBucket` S3 bucket (use `bucket.grant_write(task_role)`).
            *   Permissions to pull secrets from Secrets Manager if used for Git tokens (e.g., `secretsmanager.Secret.from_secret_name_v2(...).grant_read(task_role)`).
            *   Permissions for CloudWatch Logs (usually added automatically by `ecs.FargateTaskDefinition`).
            *   *Consider:* Permissions for CodeCommit/GitHub access if needed for cloning private repos.
    *   **Fargate Task Definition:**
        *   Define an `ecs.FargateTaskDefinition`.
        *   Assign the `task_role` created above.
        *   Specify CPU and Memory limits (e.g., `cpu=1024`, `memory_limit_mib=2048` - adjust based on expected workload).
    *   **Container Definition (within Task Definition):**
        *   Use `task_definition.add_container(...)`.
        *   Specify an `image`. For now, use a placeholder public image like `ecs.ContainerImage.from_registry("public.ecr.aws/amazonlinux/amazonlinux:latest")`. We will build and push our actual application image later.
        *   Enable `logging` using `ecs.LogDrivers.aws_logs(...)` to send container logs to CloudWatch Logs. Configure a log group and stream prefix.
        *   Define necessary environment variables (can be added later when the container logic is defined).

3.  **Synthesize Stack:**
    *   Run `cdk synth` from the CDK project directory (`iac/`) to ensure the stack synthesizes correctly without errors.

**Reference:** Consult `plan.md` (Phase 3, Step 1) for the overall context.
