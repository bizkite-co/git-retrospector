# Task: Fix Git Lambda Layer for HTTPS Support (Phase 3 - Fix)

**Objective:** Modify the Git Lambda Layer build process or find an alternative layer to include HTTPS support, resolving the `git: 'remote-https' is not a git command` error encountered during `git clone` in the Initiation Lambda.

**Context:** The previous invocation test failed because the attached Git Lambda Layer was incomplete. It lacked the `git-remote-https` helper and its dependencies (like `curl`, `ca-certificates`), preventing Git from cloning repositories over HTTPS.

**Prerequisites:**
*   CDK project (`iac/`) deployed, including the Initiation Lambda attached to the currently faulty Git Layer.
*   Method for building/defining the Git Layer identified (e.g., custom `Dockerfile` in `lambda_layers/git/` or a public ARN was used).

**Detailed Steps:**

1.  **Identify Layer Source:** Confirm how the current Git Layer was defined in `iac/iac/iac_stack.py` (custom asset zip or public ARN).

2.  **Modify Layer Build/Source:**
    *   **If using Custom Layer (e.g., `lambda_layers/git/Dockerfile`):**
        *   Edit the `Dockerfile` used to build the layer.
        *   Ensure `yum install` (or equivalent for the base image, likely `amazonlinux:2`) includes `git`, `curl`, and `ca-certificates`.
        *   Verify that the process copies not just `/usr/bin/git` but also `/usr/libexec/git-core/git-remote-https` (or similar path) into the `/opt/libexec/git-core/` directory within the layer structure.
        *   Verify that necessary shared libraries identified by `ldd /usr/libexec/git-core/git-remote-https` (especially those related to `curl` and `ssl`) are copied into `/opt/lib/`.
        *   Re-build the layer zip file using the updated Dockerfile.
    *   **If using Public Layer ARN:**
        *   The current layer is insufficient. Search again for a *different* public Git Lambda Layer specifically advertised as including HTTPS support and compatible with the `python3.11` (Amazon Linux 2) runtime in `us-east-1`. Look for layers on SAR or reputable community projects.
        *   If a suitable alternative public ARN is found, update the ARN used in `lambda_.LayerVersion.from_layer_version_arn(...)` in `iac/iac/iac_stack.py`.
        *   If no suitable public layer is found, switch to building a custom layer (Option B above).

3.  **Update CDK Stack (If Necessary):**
    *   If using a custom layer, ensure the `lambda_.LayerVersion` construct points to the *newly built* zip file asset.
    *   If switching to a different public ARN, update the ARN in the CDK code.
    *   **Add `GIT_EXEC_PATH` environment variable to the Initiation Lambda.**

4.  **Synthesize and Deploy:**
    *   Run `cdk synth` from the `iac/` directory. Verify it synthesizes correctly.
    *   Run `cdk deploy --require-approval never`. Monitor the deployment (it should update the Lambda function's layer configuration).

5.  **Re-Test Invocation:**
    *   After successful deployment, re-run the `aws lambda invoke` command using your script (`invoke-retrospector.sh`).
    *   Check the Initiation Lambda logs again. Does the `git clone` command now succeed without the `remote-https` error? Does the execution proceed further (e.g., attempting to get commit list, update DynamoDB, start Step Function)?

**Reference:** Consult `plan.md` (Phase 3). This addresses the blocker identified in the previous invocation test.

---

**Achievements:**

*   Confirmed the Git Layer uses a custom asset (`lambda_layers/git/git-layer.zip`).
*   Updated `lambda_layers/git/Dockerfile` to install `curl`, `ca-certificates`, copy `curl` binary, update CA trust, and improve dependency discovery for `git`, `curl`, and `git-remote-https`.
*   Rebuilt the `git-layer.zip` using the updated Dockerfile.
*   Updated `iac/iac/iac_stack.py` to add the `GIT_EXEC_PATH=/opt/libexec/git-core` environment variable to the Initiation Lambda.
*   Successfully deployed the updated CDK stack twice (first with layer changes, second with environment variable change).
*   Updated `get-retro-logs.sh` to dynamically find the correct Initiation Lambda log group name.
*   Verified via Lambda logs that the `git clone` command using HTTPS now succeeds.
