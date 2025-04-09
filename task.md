# Task: Create Dockerfile for Fargate Task (Phase 3 - Step 3a)

**Objective:** Create the `Dockerfile` to build the container image that will run the Fargate task logic (`process_single_commit_task.py`).

**Context:** This defines the runtime environment for the core processing logic within ECS Fargate.

**Prerequisites:**
*   Fargate task script exists at `fargate_task/process_single_commit_task.py`.
*   Dependencies for the script are listed in `fargate_task/requirements.txt`.

**Detailed Steps:**

1.  **Create `Dockerfile`:**
    *   Create a new file named `Dockerfile` inside the `fargate_task/` directory.
    *   **DONE:** `fargate_task/Dockerfile` created.

2.  **Define Dockerfile Stages:**
    *   **Base Stage:**
        *   Start from a suitable Python base image (e.g., `FROM python:3.11-slim`).
        *   Set the working directory (e.g., `WORKDIR /app`).
        *   Install necessary OS packages:
            *   Update package lists (`apt-get update`).
            *   Install `git` (`apt-get install -y git`).
            *   Install `curl` or `wget` if needed for fetching `uv`.
            *   Clean up apt cache (`rm -rf /var/lib/apt/lists/*`).
        *   Install `uv`: Download the installer script and execute it, or download the binary directly. Ensure it's executable and in the PATH.
            ```dockerfile
            # Example using installer script (check for latest URL/method)
            RUN apt-get update &amp;&amp; apt-get install -y curl &amp;&amp; \
                curl -LsSf https://astral.sh/uv/install.sh | sh &amp;&amp; \
                apt-get purge -y --auto-remove curl &amp;&amp; \
                rm -rf /var/lib/apt/lists/*
            ENV PATH="/root/.cargo/bin:$PATH" # Note: Actual install path was /root/.local/bin
            ```
    *   **Application Stage:**
        *   Copy the requirements file (`COPY requirements.txt .`).
        *   Install Python dependencies using `uv`: `RUN uv pip install --no-cache --system -r requirements.txt`.
        *   Copy the Fargate task script (`COPY process_single_commit_task.py .`).
        *   *(Consideration):* If shared code from `src/git_retrospector` is needed and not included via dependencies, copy it here as well. This might involve adjusting paths or packaging `git_retrospector` as an installable library. For now, assume the script is self-contained or dependencies handle shared code.
        *   Define the entrypoint or command to run the script (e.g., `CMD ["python", "process_single_commit_task.py"]`).
    *   **DONE:** Stages defined in `fargate_task/Dockerfile`. Corrected `uv` PATH to `/root/.local/bin`.

3.  **(Optional) Local Build Test:**
    *   Navigate to the `fargate_task/` directory.
    *   Run `docker build -t retrospector-fargate-task .` to verify the Dockerfile builds successfully locally.
    *   **DONE:** Build tested successfully after manual correction of `&amp;&amp;` syntax issue.

**Reference:** Consult `plan.md` (Phase 3, Step 3).

**Achievements (2025-04-08):**
*   Created `fargate_task/Dockerfile`.
*   Defined base and application stages.
*   Installed OS packages (git) and Python package manager (`uv`).
*   Installed Python dependencies from `fargate_task/requirements.txt`.
*   Set up the entrypoint for `process_single_commit_task.py`.
*   Corrected `uv` installation path in `ENV PATH`.
*   Successfully built the Docker image locally (`retrospector-fargate-task:latest`) after manual correction of `&amp;&amp;` syntax in the `RUN` command.
