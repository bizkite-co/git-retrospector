# Task: Create Initiation Lambda Function (Phase 3 - Step 2a)

**Objective:** Create the AWS Lambda function responsible for initiating the retrospector workflow. This function will fetch the commit list, populate DynamoDB, and start the Step Functions execution.

**Context:** This is the first part of refactoring the application logic for AWS (Phase 3, Step 2). It connects the user request/trigger to the Step Functions workflow.

**Prerequisites:**
*   CDK stack (`iac/iac/iac_stack.py`) defines DynamoDB table (`CommitStatusTable`) and Step Functions State Machine (`RetrospectorStateMachine`).

**Detailed Steps:**

1.  **Create Lambda Function Code:**
    *   Create a new directory for Lambda function code, e.g., `lambda_fns/initiation/`.
    *   Inside this directory, create a Python file for the handler, e.g., `handler.py`.
    *   **Handler Logic (`handler.py`):**
        *   Import necessary libraries: `boto3`, `os`, `json`, `datetime`.
        *   Import relevant logic from the main `git_retrospector` project, specifically the adapted `get_commit_list` function (or reimplement the `git log` call directly if simpler, but ensure format consistency). *Note:* This Lambda will need `git` installed or access to a Git layer/container. Alternatively, consider using a library like `GitPython` if feasible, or calling out to a separate Fargate task just for the `git log` if `git` is too heavy for Lambda. **Let's start assuming `git` is available via a layer or custom runtime for simplicity, but be prepared to revise.**
        *   Define the Lambda handler function (e.g., `lambda_handler(event, context)`).
        *   Parse input `event` to get `repo_owner`, `repo_name`, `repo_url` (needed for cloning), and selection criteria (e.g., `iterations`).
        *   Retrieve Git credentials/token securely (e.g., from environment variables passed by CDK, or from Secrets Manager).
        *   **Crucially:** Clone the target repository into the Lambda's temporary storage (`/tmp`). This has size/time limits.
        *   Call the adapted `get_commit_list` logic using the cloned repo path and selection criteria.
        *   Get references to the DynamoDB table name and State Machine ARN from environment variables (these will be passed by CDK).
        *   Initialize `boto3` clients for DynamoDB (`dynamodb = boto3.resource('dynamodb')`) and Step Functions (`sfn = boto3.client('stepfunctions')`).
        *   Get the DynamoDB table object: `table = dynamodb.Table(os.environ['COMMIT_STATUS_TABLE_NAME'])`.
        *   Iterate through the fetched `commit_list`:
            *   For each commit, use `table.put_item` to create an entry in DynamoDB with `repo_id`, `commit_hash`, `commit_date`, `commit_summary`, and initial `status='PENDING'`. Consider using BatchWriteItem for efficiency if the list is large.
        *   Prepare the initial input for the Step Functions state machine (e.g., including `repo_owner`, `repo_name`, `repo_url`, and the fetched `commits` list).
        *   Start the Step Functions execution using `sfn.start_execution`, passing the `stateMachineArn` and the prepared `input`.
        *   Return a success response.
        *   Include error handling (try/except blocks) for Git operations, DynamoDB writes, and Step Functions calls.
    *   Create a `requirements.txt` (or use `pyproject.toml` with `uv`) for Lambda dependencies (e.g., `boto3`, potentially `GitPython`).

2.  **Define Lambda in CDK Stack (`iac/iac/iac_stack.py`):**
    *   Import `aws_lambda` and potentially `aws_lambda_python_alpha` for easier bundling.
    *   Define an `aws_lambda.Function` or `aws_lambda_python_alpha.PythonFunction`.
        *   Set `runtime` (e.g., `lambda_.Runtime.PYTHON_3_11`).
        *   Set `handler` (e.g., `handler.lambda_handler`).
        *   Set `code` pointing to the `lambda_fns/initiation/` directory. (`aws_lambda_python_alpha` handles bundling automatically).
        *   Pass environment variables:
            *   `COMMIT_STATUS_TABLE_NAME`: The name of the DynamoDB table (`table.table_name`).
            *   `STATE_MACHINE_ARN`: The ARN of the Step Functions state machine (`state_machine.state_machine_arn`).
            *   Potentially Git token secret ARN or name.
        *   Grant necessary permissions to the Lambda's execution role:
            *   DynamoDB write access: `table.grant_write_data(lambda_function)`.
            *   Step Functions start execution: `state_machine.grant_start_execution(lambda_function)`.
            *   Secrets Manager read access if used.
            *   Consider permissions needed for cloning (e.g., CodeCommit or accessing public internet for GitHub).
        *   Increase `timeout` if needed (default is 3 seconds, cloning might take longer). Max is 15 mins.
        *   Increase `memory_size` if needed.
        *   **(Optional/Advanced):** Configure a Lambda Layer containing the `git` binary if not using a custom runtime or `GitPython`.

3.  **Update Step Functions Definition (CDK):**
    *   Replace the placeholder "Initiation" `sfn.Pass` state with an `sfn_tasks.LambdaInvoke` state that invokes the newly created Lambda function.
    *   Adjust the state machine definition chain accordingly.

4.  **Synthesize Stack:**
    *   Run `cdk synth` to ensure the stack synthesizes correctly.

**Reference:** Consult `plan.md` (Phase 3, Step 2a).

---
**Achievements (2025-04-08):**
*   Created Lambda handler code in `lambda_fns/initiation/handler.py`.
*   Created `lambda_fns/initiation/requirements.txt`.
*   Added `aws-cdk.aws-lambda-python-alpha` dependency to `iac/requirements.txt`.
*   Defined Initiation Lambda function (`InitiationLambda`) in `iac/iac/iac_stack.py` using `PythonFunction`.
*   Granted necessary DynamoDB write and Step Functions start execution permissions to the Lambda role.
*   Updated the Step Functions definition in the CDK stack to be triggered by the Lambda (Lambda calls `start_execution`).
*   Successfully synthesized the CDK stack (`cdk synth`).
