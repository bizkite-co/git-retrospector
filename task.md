# Task: Fix Step Function Environment Variable Passing to Fargate Task

**Objective:** Modify the AWS CDK stack (`iac/iac/iac_stack.py`) to ensure *all* required environment variables (`REPO_ID`, `COMMIT_HASH_TO_PROCESS`, `REPO_OWNER`, `REPO_NAME`, `REPO_URL`) are correctly passed from the Step Function context to the `ProcessSingleCommitTask` (EcsRunTask) state's container environment.

**Context:**
The previous fix attempted to resolve an input mapping issue for `repo_id`. While the initial invocation succeeded, subsequent log analysis revealed that the Fargate task (`process_single_commit_task.py`) is still failing because it's not receiving expected environment variables like `REPO_OWNER`, `REPO_NAME`, and `REPO_URL`. The `container_overrides` section within the `EcsRunTask` definition needs to be updated to include these variables, pulling them from the main Step Function input payload (which is populated by the Initiation Lambda).

**Prerequisites:**
*   CDK project (`iac/`) deployed with the previous (partially successful) fix.
*   Understanding of which environment variables the `fargate_task/process_single_commit_task.py` script requires. (Assuming `REPO_OWNER`, `REPO_NAME`, `REPO_URL`, `REPO_ID`, `COMMIT_HASH_TO_PROCESS`, `DYNAMODB_TABLE_NAME`, `S3_BUCKET_NAME`).

**Detailed Steps:**

1.  **Modify `iac/iac/iac_stack.py`:**
    *   Locate the `fargate_task_state = sfn_tasks.EcsRunTask(...)` definition (around line 170).
    *   Verify the `parameters` field correctly includes `repo_id` and `commit_details` (as implemented in the previous attempt). It should also include owner, name, and url if the task needs direct access to the *original* input values, distinct from the container env vars.
        ```python
        parameters={
            "commit_details.$": "$$.Map.Item.Value",
            "repo_id.$": "$.repo_id",
            # Also pass owner, name, url from top-level input
            "repo_owner.$": "$.repo_owner",
            "repo_name.$": "$.repo_name",
            "repo_url.$": "$.repo_url" # Assuming the Fargate task might need the original clone URL context
        },
        ```
    *   Focus on the `container_overrides` -> `environment` list within the `EcsRunTask` definition.
    *   Ensure `TaskEnvironmentVariable` entries exist for **all** required variables passed via overrides:
        *   `REPO_ID`: Value should be `sfn.JsonPath.string_at("$.repo_id")` (referencing the `parameters` field).
        *   `COMMIT_HASH_TO_PROCESS`: Value should be `sfn.JsonPath.string_at("$.commit_details.commit_hash")` (referencing the `parameters` field).
        *   `REPO_OWNER`: Add/ensure this exists with value `sfn.JsonPath.string_at("$.repo_owner")` (referencing the `parameters` field).
        *   `REPO_NAME`: Add/ensure this exists with value `sfn.JsonPath.string_at("$.repo_name")` (referencing the `parameters` field).
        *   `REPO_URL`: Add/ensure this exists with value `sfn.JsonPath.string_at("$.repo_url")` (referencing the `parameters` field).
        *   `DYNAMODB_TABLE_NAME`: This should already be set directly on the main `container` definition (around line 163) and doesn't need to be overridden here unless the value needs to be dynamic per task invocation (which is unlikely). Double-check it's present on the main container definition.
        *   `S3_BUCKET_NAME`: Similar to DynamoDB, check this is set on the main `container` definition (around line 164).

    *Example Code Snippet (Illustrative - focusing on environment overrides):*
    ```python
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
                        value=sfn.JsonPath.string_at("$.commit_details.commit_hash"),
                    ),
                    # --- Add/Ensure these ---
                    sfn_tasks.TaskEnvironmentVariable(
                        name="REPO_OWNER",
                        value=sfn.JsonPath.string_at("$.repo_owner"),
                    ),
                    sfn_tasks.TaskEnvironmentVariable(
                        name="REPO_NAME",
                        value=sfn.JsonPath.string_at("$.repo_name"),
                    ),
                    sfn_tasks.TaskEnvironmentVariable(
                        name="REPO_URL",
                        value=sfn.JsonPath.string_at("$.repo_url"),
                    ),
                    # --- End Add/Ensure ---
                ],
            )
        ],
    ```

2.  **Synthesize and Deploy:**
    *   Navigate to the `iac/` directory.
    *   Run `cdk synth`. Verify it synthesizes correctly.
    *   Run `cdk deploy --require-approval never`. Monitor the deployment.

3.  **Re-Test Invocation:**
    *   Run the `invoke-retrospector.sh` script again.
    *   Execute `./get-retro-logs.sh`.
    *   Analyze the Step Function and Fargate task logs carefully. Verify the Fargate task now receives *all* required environment variables and proceeds with its logic without failing due to missing variables. Check for successful commit processing logs.

**Reference:** This task aims to fully resolve the environment variable passing issue between the Step Function and the Fargate task.

---

**Achievements (2025-04-09):**

*   Identified that the root cause of the missing environment variables (`REPO_OWNER`, `REPO_NAME`, `REPO_URL`) in the Fargate task was that the Initiation Lambda was not including `repo_url` in the input payload sent to the Step Function.
*   Implemented a simplification strategy based on user feedback:
    *   Modified the Initiation Lambda (`lambda_fns/initiation/handler.py`) to only pass `repo_url` and `commits` to the Step Function.
    *   Modified the CDK stack (`iac/iac/iac_stack.py`) to update the Step Function's `Map` state parameters and the `EcsRunTask` container overrides to only handle `repo_url` and `commit_details`.
    *   Modified the Fargate task script (`fargate_task/process_single_commit_task.py`) to expect only `REPO_URL` and `COMMIT_HASH_TO_PROCESS` as environment variables, and to parse the `repo_owner` and `repo_name` from the provided `REPO_URL`.
*   Successfully deployed the updated infrastructure using `cdk deploy`.
*   Successfully re-tested the invocation using `invoke-retrospector.sh` and `./get-retro-logs.sh`.
*   Verified from the logs that the Fargate task now receives the necessary `REPO_URL`, parses the owner/name correctly, and completes the processing successfully.
