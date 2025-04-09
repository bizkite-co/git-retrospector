# Task: Implement Fargate Task Logic Script (Phase 3 - Step 2b)

**Objective:** Create the Python script that will execute within the Fargate container to process a single commit.

**Context:** This script represents the core workhorse of the parallel processing workflow defined in the Step Functions state machine. It takes details for a single commit, processes it, and updates the central state/results.

**Prerequisites:**
*   CDK stack defines DynamoDB table, S3 bucket, and Fargate Task Definition.
*   Initiation Lambda populates DynamoDB and triggers the Step Functions workflow.
*   The Fargate Task Definition (within the Step Functions Map state) is configured to pass `repo_owner`, `repo_name`, `repo_url`, and `commit_hash` to the container (e.g., via environment variables like `REPO_OWNER`, `REPO_NAME`, `REPO_URL`, `COMMIT_HASH_TO_PROCESS`).

**Detailed Steps:**

1.  **Create Fargate Script Directory & File:**
    *   Create a new directory, e.g., `fargate_task/`.
    *   Inside, create the main script file, e.g., `process_single_commit_task.py`.

2.  **Implement Script Logic (`process_single_commit_task.py`):**
    *   **Import necessary libraries:** `os`, `subprocess`, `boto3`, `json`, `logging`, `shutil`, `pathlib`.
    *   **Import relevant logic:** Adapt and import necessary functions from the main `git_retrospector` project (e.g., parts of `commit_processor.py`, `retro.py` related to running tests, parsing results, potentially `git_utils`). *Carefully consider dependencies and how to package/access this shared code within the container.* (For now, assume functions can be copied/adapted into this script or a shared layer).
    *   **Setup Logging:** Configure basic logging.
    *   **Retrieve Input:** Get `repo_owner`, `repo_name`, `repo_url`, `commit_hash`, `table_name`, `bucket_name` from environment variables (e.g., `os.environ.get(...)`). Add error handling if variables are missing.
    *   **Initialize Boto3 Clients:** Create clients for DynamoDB and S3. Get the DynamoDB table resource.
    *   **Update Status (RUNNING):** Update the item in DynamoDB for the current `repo_id` (`owner/name`) and `commit_hash` to set `status='RUNNING'`. Include error handling.
    *   **Define Local Paths:** Define paths within the container's temporary filesystem (e.g., `/app/repo`, `/app/output`).
    *   **Clone Repository:**
        *   Retrieve Git credentials securely if needed (e.g., from environment variables or Secrets Manager - requires IAM permissions).
        *   Use `subprocess.run` to clone the `repo_url` into the defined local repo path. Handle errors.
    *   **Checkout Commit:** Use `subprocess.run` to `git checkout` the specific `commit_hash` within the cloned repo. Handle errors.
    *   **Run Test Runners:**
        *   *Adaptation Required:* The concept of `retro.toml` needs rethinking. Test runner commands might need to be passed via environment variables, discovered from the repo, or standardized. **Simplification for now:** Assume test commands are known or passed via environment variables.
        *   Execute the test command(s) using `subprocess.run` (similar to `retro.run_tests`), capturing output. Store results in the defined local output path.
    *   **Parse Results:**
        *   *Adaptation Required:* Adapt the result parsing logic (e.g., from `parser.py`) to read files from the local output path.
        *   Calculate `total_tests`, `failed_tests`.
    *   **Upload Results to S3:**
        *   Use `boto3` S3 client (`upload_file` or potentially syncing the whole output directory) to upload the contents of the local output directory to `s3://<bucket_name>/<repo_owner>/<repo_name>/<commit_hash>/`. Handle errors. Construct the `s3_output_path`.
    *   **Update Status (COMPLETE/FAILED):**
        *   Update the item in DynamoDB for the current commit:
            *   Set `status='COMPLETE'`.
            *   Set `total_tests`, `failed_tests`.
            *   Set `s3_output_path`.
        *   If any step failed, update status to `'FAILED'` and log errors appropriately.
    *   **Cleanup:** Remove the cloned repository and local output directories from the container's filesystem.
    *   **Main Execution Block:** Use `if __name__ == "__main__":` to call the main processing logic.

3.  **Create `requirements.txt`:**
    *   In the `fargate_task/` directory, list dependencies needed specifically by this script (e.g., `boto3`).

**Considerations:**
*   **Shared Code:** How will functions from `git_retrospector` be made available to this script? (Copying, packaging as a library, Lambda layer?)
*   **Test Runner Config:** How will the script know which test commands to run? (Environment variables, file in repo?)
*   **Error Handling:** Robust error handling is critical for each step (Git, tests, S3, DynamoDB). Failures should result in a 'FAILED' status in DynamoDB.

**Reference:** Consult `plan.md` (Phase 3, Step 2b).

**Status:**
*   [X] Initial implementation of `fargate_task/process_single_commit_task.py` created.
*   [X] `fargate_task/requirements.txt` created with `boto3` dependency.
*   [ ] Integration of shared code from `git_retrospector` needed.
*   [ ] Specific test result parsing logic needs implementation.
