# Refactoring Plan: Improve Commit Selection and Reporting

This plan outlines the steps to refactor the `git-retrospector` tool to pre-fetch commit information, making the process more robust and enabling richer data association.

## Phase 1: Pre-fetch Commits by Iteration Count

**Goal:** Replace the current iterative commit discovery with a pre-fetch mechanism based on the iteration count. Store commit hash, date, and summary. Replace `commits.log` with `commit_manifest.json`.

**Steps:**

1.  **Modify `src/git_retrospector/git_utils.py`:**
    *   Add a new function `get_commit_list(repo_path, num_commits)`.
    *   Use `subprocess.run` with `git log --pretty=format:'%H|%ad|%s' --date=iso -n <num_commits>`.
    *   Parse the output (split by newline, then by '|') to return a list of dictionaries, each containing `hash`, `date`, and `summary`. Example: `[{'hash': '...', 'date': '...', 'summary': '...'}, ...]`.

2.  **Refactor `src/git_retrospector/retrospector.py` (`run_tests` function):**
    *   Remove the existing loop that calls `git rev-parse`.
    *   Call the new `get_commit_list(target_repo, iteration_count)` function *before* the loop to get the list of commits.
    *   Store the returned list.
    *   Define the path for the new manifest file: `manifest_path = Path(retro.get_test_output_dir()) / "commit_manifest.json"`.
    *   Write the fetched commit list to `manifest_path` using `json.dump()`. Ensure the directory exists.
    *   Iterate through the *stored list* of commits.
    *   Inside the loop, extract the `commit_hash` from the current item in the list.
    *   Pass the `commit_hash` to `process_single_commit`.
    *   Remove the old logic for writing to `commits.log`.

3.  **Refactor `src/git_retrospector/commit_processor.py` (`process_commit` function):**
    *   Review the function signature and logic. No immediate changes are required for this phase, as it primarily needs the `commit_hash`. However, keep in mind that more data (date, summary) is now available upstream if needed in the future.

4.  **CLI (`@click` commands in `retrospector.py`):**
    *   No changes are needed for the `run` command's options in this phase, as we are only changing the *implementation* for the existing `iterations` parameter.

**Diagram:**

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
    M --> N[End];

    subgraph Future Enhancements
        C -- Add Params --> C;
        G -- Pass More Data --> G;
        A -- Add CLI Options --> A;
    end

    style E fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#ccf,stroke:#333,stroke-width:2px
    style G fill:#ccf,stroke:#333,stroke-width:2px
```

## Phase 2: Future Enhancements (Out of Scope for Initial Refactor)

*   Add support for other commit selection methods (date ranges, specific hashes) via new CLI options and updates to `get_commit_list`.
*   Enhance `commit_manifest.json` to store test results (total tests, failures) alongside commit data.
*   Pass additional commit data (date, summary) down to `process_commit` if needed for reporting or logic.
*   Implement the AWS Step Function/Fargate/S3 architecture for parallel processing.
