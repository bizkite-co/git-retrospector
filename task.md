# Task: Integrate Docker Image Build into CDK (Phase 3 - Step 3b)

**Objective:** Update the CDK stack to automatically build the Docker image from `fargate_task/Dockerfile`, push it to ECR, and configure the Fargate Task Definition to use this image.

**Context:** This connects the `Dockerfile` definition to the Fargate compute environment defined in CDK, replacing the placeholder image.

**Prerequisites:**
*   `Dockerfile` exists at `fargate_task/Dockerfile`.
*   CDK stack (`iac/iac/iac_stack.py`) defines the Fargate Task Definition with a placeholder container image.
*   `aws_ecr_assets` library is installed in the CDK project's virtual environment (was installed in Step 1b).

**Detailed Steps:**

1.  **Update `iac/iac/iac_stack.py`:**
    *   Import `aws_ecr_assets as ecr_assets`.
    *   **Define Docker Image Asset:**
        *   Create an instance of `ecr_assets.DockerImageAsset`.
        *   Provide an `id` (e.g., "RetrospectorFargateTaskImage").
        *   Set the `directory` parameter to the path containing the `Dockerfile` (e.g., `os.path.join(os.path.dirname(__file__), "..", "fargate_task")` or use `pathlib`).
    *   **Update Fargate Task Definition's Container:**
        *   Locate the `.add_container(...)` call within the Fargate Task Definition.
        *   Modify the `image` parameter: Instead of the placeholder (`ecs.ContainerImage.from_registry(...)`), use the image asset: `image=ecs.ContainerImage.from_docker_image_asset(docker_image_asset)`. (Where `docker_image_asset` is the variable holding the `DockerImageAsset` instance).

2.  **Synthesize Stack:**
    *   Run `cdk synth` from the CDK project directory (`iac/`). Verify it synthesizes correctly. The output should now reference the ECR image asset.

3.  **(Informational) Deployment Note:**
    *   When `cdk deploy` is run later, CDK will:
        *   Build the Docker image using the Docker daemon running on the deployment machine.
        *   Tag the image.
        *   Authenticate to ECR.
        *   Push the image to the ECR repository automatically created by the asset construct.
        *   Update the Fargate Task Definition in the CloudFormation template to reference the specific ECR image URI (including the tag/digest).
    *   Ensure Docker is running on the machine where `cdk deploy` will be executed.

**Reference:** Consult `plan.md` (Phase 3, Step 3).
