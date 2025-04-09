# Refactoring Plan: Improve Commit Selection and Reporting

This plan outlines the steps to refactor the `git-retrospector` tool to pre-fetch commit information, making the process more robust and enabling richer data association, and finally migrating it to a scalable AWS architecture.

## Phase 1: Pre-fetch Commits by Iteration Count (Completed)

**Goal:** Replace the current iterative commit discovery with a pre-fetch mechanism based on the iteration count. Store commit hash, date, and summary. Replace `commits.log` with `commit_manifest.json`. Ensure changes are tested.
**Status:** Completed.

## Phase 2: Local Enhancements (Deferred)

**Goal:** Enhance the local version with more features before migrating to AWS.
**Status:** Deferred until after Phase 3 initial setup/testing.

## Phase 3: Migration to AWS Serverless Architecture (In Progress)

**Goal:** Migrate the retrospector tool to a scalable, parallel processing architecture on AWS using CDK, Step Functions, Fargate, S3, and DynamoDB.

**Current Status:**
*   Core infrastructure (DynamoDB, S3, ECS Cluster, Fargate Task Def, Step Function structure, Initiation Lambda, Dockerfile, ECR Asset integration) defined in CDK.
*   Stack renamed to `RetrospectorInfraStack`.
*   Git Lambda Layer added to Initiation Lambda.
*   Initial deployment successful.
*   **Blocker Resolved (Git Layer):** Git Lambda Layer was fixed to include HTTPS support. `git clone` in Initiation Lambda now works.
*   **Blocker Resolved (Input Mapping):** Step Function `Map` state input mapping fixed to correctly pass `repo_id` and other necessary details (`repo_owner`, `repo_name`, `repo_url`) to the `EcsRunTask` iterator using the `Map` state's `parameters` field and `EcsRunTask`'s `container_overrides`.
*   **Blocker Resolved (Architecture):** Fargate task `exec format error` resolved by specifying `platform=ecr_assets.Platform.LINUX_AMD64` for the `DockerImageAsset` build.
*   **Current Status:** The latest deployment includes fixes for input mapping and container architecture. The next step is to re-run the invocation test.

**Next Step:** Re-test the invocation (`invoke-retrospector.sh`) to verify the Fargate task runs successfully with the correct environment variables.

**Planned Steps:**

1.  **Define AWS Infrastructure (CDK):**
    *   Create CDK project/stack (`iac/`). (Done)
    *   Rename stack to `RetrospectorInfraStack`. (Done)
    *   Define DynamoDB Table (`CommitStatusTable`). (Done)
    *   Define S3 Bucket (`ResultsBucket`). (Done)
    *   Define ECS Cluster. (Done)
    *   Define Fargate Task Definition (`RetrospectorTaskDef`) w/ IAM Role & correct platform. (Done)
    *   Define Step Functions State Machine (`RetrospectorStateMachine`) structure with correct input mapping. (Done)
    *   Define Git Lambda Layer. (Done)
        *   **Fix Git Lambda Layer:** Ensure layer includes `git-remote-https` helper and dependencies (`curl`, `ca-certificates`). (Done)
    *   Define Initiation Lambda Function & attach Git Layer. (Done)
    *   Integrate Docker Image build (`fargate_task/Dockerfile`) via ECR Assets into Task Definition with correct platform. (Done)
    *   *(Future):* Define API Gateway trigger for Initiation Lambda.

2.  **Refactor Application Logic for AWS:**
    *   **Initiation Logic (Lambda):** (Implemented)
    *   **Fargate Task Logic (Container Script):** (Implemented)

3.  **Containerization:**
    *   Create `Dockerfile` for Fargate task. (Done)

4.  **Deployment & Testing:**
    *   Initial CDK Deployment. (Done)
    *   Basic Invocation Test. (Done, subsequent failures investigated and fixed)
    *   Re-test Invocation after Environment Variable fix. (Pending - **NEXT ACTION**)
    *   Develop unit tests for Lambda/Fargate logic. (Pending)
    *   Perform integration testing. (Pending)
    *   Conduct end-to-end tests. (Pending)
    *   Update `get-retro-logs.sh` to include Fargate task logs. (Pending)

**Level of Effort (LoE) Estimate:** (Unchanged) High.
**Timeline:** (Unchanged) Several weeks to 1-2 months.
**Revised Estimated Gemini Cost (Planning Phase 3):** $2.00 - $4.00 (Excludes implementation assistance & AWS costs).
