# Refactoring Plan: Improve Commit Selection and Reporting

This plan outlines the steps to refactor the `git-retrospector` tool to pre-fetch commit information, making the process more robust and enabling richer data association, and finally migrating it to a scalable AWS architecture.

## Phase 1: Pre-fetch Commits by Iteration Count (Completed)

**Goal:** Replace the current iterative commit discovery with a pre-fetch mechanism based on the iteration count. Store commit hash, date, and summary. Replace `commits.log` with `commit_manifest.json`. Ensure changes are tested.

**Status:** Completed.

**Steps:**

1.  **Modify `src/git_retrospector/git_utils.py`:** (Done)
2.  **Refactor `src/git_retrospector/retrospector.py` (`run_tests` function):** (Done)
3.  **Refactor `src/git_retrospector/commit_processor.py` (`process_commit` function):** (Reviewed, no changes needed for Phase 1)
4.  **CLI (`@click` commands in `retrospector.py`):** (No changes needed for Phase 1)
5.  **Testing:** (Done)
6.  **Bug Fix:** Fixed `TypeError` for `TestRunner` attribute access. (Done)

**Diagram (Phase 1):**

```mermaid
graph TD
    A[Start run command] --> B{Load Retro Config};
    B --> C[Call git_utils.get_commit_list(iterations)];
    C --> D{Store List of Commits (Hash, Date, Summary)};
    D --> E[Write commit list to commit_manifest.json];
    E --> F{Loop through Commit List};
    F -- For Each Commit --> G[Call retrospector.process_single_commit(commit_hash)];
    G --> H[commit_processor.process_commit];
    H --> I[Checkout Commit];
    I --> J[Run Tests];
    J --> K[Collect Results];
    K --> F;
    F -- Loop Finished --> L[Checkout Original Branch (if not --keep)];
    L --> M[Analyze Results];
    M --> N[Run Unit Tests]; %% Added Test Step
    N --> O[End]; %% Shifted End

    subgraph Future Enhancements (Now Phase 2/3)
        C -- Add Params --> C;
        G -- Pass More Data --> G;
        A -- Add CLI Options --> A;
    end

    style E fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#ccf,stroke:#333,stroke-width:2px
    style G fill:#ccf,stroke:#333,stroke-width:2px
    style N fill:#cfc,stroke:#333,stroke-width:2px %% Style Test Step
```

## Phase 2: Local Enhancements

**Goal:** Enhance the local version with more features before migrating to AWS.

**Steps:**

*   Add support for other commit selection methods (date ranges, specific hashes) via new CLI options and updates to `get_commit_list`.
*   Enhance `commit_manifest.json` or reporting mechanism to store aggregated test results (total tests, failures) alongside commit data after parsing.
*   Pass additional commit data (date, summary) down to `process_commit` if needed for reporting or logic.

## Phase 3: Migration to AWS Serverless Architecture

**Goal:** Migrate the retrospector tool to a scalable, parallel processing architecture on AWS using CDK, Step Functions, Fargate, S3, and DynamoDB.

**Steps:**

1.  **Define AWS Infrastructure (CDK):**
    *   Create a new AWS CDK project/stack (e.g., in `iac/`).
    *   *Note on Dependency Management:* The default `cdk init` uses `pip`. While functional, consider switching to `uv` later if dependency installation speed becomes an issue within the CDK project.
    *   **DynamoDB Table (`CommitStatusTable`):** (Defined in Step 1a)
        *   Purpose: Replace `commit_manifest.json`, track state for parallel execution.
        *   Schema Suggestion: PK: `repo_id` (String), SK: `commit_hash` (String), Attributes: `status` (String), `total_tests` (Number), `failed_tests` (Number), `commit_date` (String/ISO), `commit_summary` (String), `s3_output_path` (String).
    *   **S3 Bucket (`ResultsBucket`):** (Defined in Step 1a)
        *   Purpose: Store raw test output artifacts.
        *   Structure: `s3://<bucket-name>/<repo_owner>/<repo_name>/<commit_hash>/`.
    *   **ECS Cluster & Fargate Task Definition:** (To be defined in Step 1b)
        *   Define compute environment for running tests.
        *   Container image requirements: Git, Python, `uv`, project dependencies, `boto3`.
        *   IAM Role: Grant permissions for DynamoDB read/write, S3 write, Secrets Manager read (for Git token), potentially CodeCommit/GitHub access.
    *   **Step Functions State Machine (`RetrospectorStateMachine`):** (To be defined later)
        *   Orchestrate the overall workflow.
        *   Likely includes: Initiation step, Map state for parallel Fargate task execution, potentially error handling and aggregation steps.

2.  **Refactor Application Logic for AWS:**
    *   **Initiation Logic (Lambda Function or Initial Fargate Task):**
        *   Trigger mechanism (e.g., API Gateway, manual trigger).
        *   Input: `repo_owner`, `repo_name`, selection criteria (iterations, dates, etc.).
        *   Fetches commit list (using adapted `get_commit_list` logic).
        *   Populates `CommitStatusTable` with initial 'PENDING' status for each commit.
        *   Starts the Step Functions execution.
    *   **Fargate Task Logic (Container Script):**
        *   Input: `repo_owner`, `repo_name`, `commit_hash`.
        *   Update DynamoDB status to 'RUNNING'.
        *   Clone repository *inside the container*. (Requires Git credentials/token, potentially from Secrets Manager).
        *   Checkout specific `commit_hash`.
        *   Execute test runners (adapted `retro.run_tests`).
        *   Execute results parsing (adapted `parser.process_retro`).
        *   Calculate `total_tests`, `failed_tests`.
        *   Upload results directory (`test-output/<commit_hash>`) to S3 bucket under `<repo_owner>/<repo_name>/<commit_hash>/`.
        *   Update DynamoDB status to 'COMPLETE' or 'FAILED', including test counts and S3 path.
        *   Implement robust error handling.

3.  **Containerization:**
    *   Create `Dockerfile` installing Git, Python, dependencies (`uv install`), `boto3`.
    *   Define entrypoint script for Fargate task logic.

4.  **Deployment & Testing:**
    *   Deploy infrastructure using `cdk deploy`.
    *   Develop unit tests for new Lambda/Fargate logic.
    *   Perform integration testing with AWS services (mocking or live).
    *   Conduct end-to-end tests of the Step Functions workflow.

**Level of Effort (LoE) Estimate:**

*   **Overall:** **High**. This is a major architectural change.
*   **Breakdown:**
    *   AWS Service Learning/Configuration: Medium-High
    *   CDK Infrastructure Code: Medium-High
    *   Application Logic Refactoring: High
    *   Containerization: Low-Medium
    *   Testing (Unit, Integration, E2E): High
*   **Timeline:** Likely several weeks to 1-2 months for a developer, depending heavily on prior experience with CDK and the specific AWS services involved.

**Cost Estimate (Gemini Pro 1.5 - Planning Only):**

*   Based on observed costs (~$1.30 for implementing the first CDK step), planning the entirety of Phase 3 (which is significantly more complex) might involve several more detailed planning/refinement interactions.
*   **Revised Estimated Gemini Cost (Planning Phase 3): $2.00 - $4.00**
*   *Disclaimer:* This estimate is *only* for the AI assistance during the planning stage documented here. It does *not* include the cost of AI assistance during implementation or the runtime costs of the AWS resources (Fargate, S3, DynamoDB, Step Functions, etc.), which require separate estimation based on usage.
