# Git Retrospector - Diff Generation Plan

This document outlines the plan for implementing a feature to generate diff files for each commit in the `commits.log` file.

## Goal

The goal is to create a new feature that automatically generates diff files for each commit listed in the `commits.log` file within a retro directory. These diff files should show the changes between each commit and its *previous* commit in the log.

## Functionality

1.  **Read Commit Hashes:** Read commit hashes from the `retros/<retro_name>/commits.log` file.
2.  **Generate Diff Files:** For each commit hash (except the first one in the log), generate a diff file that shows the changes between that commit and the immediately preceding commit.
3.  **Structured Storage:** Save the generated diff files in a dedicated subdirectory within the retro directory, named `diffs`. The full path will be `retros/<retro_name>/diffs/`.
4.  **Naming Convention:** Name the diff files using the commit hashes of the two commits being compared. The format should be `<previous_commit_hash>_<current_commit_hash>.diff`. For example, `c55fc50_7849a33.diff`.
5.  **Error Handling:**
    *   Gracefully handle cases where the `commits.log` file is empty.
    *   Implement robust error checking for invalid or non-existent commit hashes. Use `git rev-parse` for validation.
    *   Raise appropriate exceptions for errors encountered during the diff generation process.
6.  **Git Command:** Utilize the `git diff` command for generating the diffs.
7.  **Commit-Specific Folders**: Place each diff file into a commit-hash-specific folder within the `diffs` directory. The structure will be `retros/<retro_name>/diffs/<current_commit_hash>/<previous_commit_hash>_<current_commit_hash>.diff`.

## Implementation Details

### 1. Helper Function (git\_utils.py)

A new helper function will be added to `src/git_retrospector/git_utils.py` to encapsulate the diff generation logic:

*   **Function Signature:** `generate_diff(repo_path: str, commit1: str, commit2: str, output_path: str) -> None`
*   **Parameters:**
    *   `repo_path`: The path to the Git repository.
    *   `commit1`: The hash of the first commit.
    *   `commit2`: The hash of the second commit.
    *   `output_path`: The full path to where the diff file should be saved.
*   **Functionality:**
    *   Validate that `commit1` and `commit2` are valid commit hashes using `git rev-parse`.
    *   Execute the `git diff` command to generate the diff between `commit1` and `commit2`.
    *   Save the output of the `git diff` command to the specified `output_path`.
    *   Handle any errors that may occur during the Git command execution.

### 2. Main Function (retrospector.py)

The core logic for reading the commit log and orchestrating the diff generation will be implemented in a new function in `src/git_retrospector/retrospector.py`:

*   **Function Signature:** `generate_commit_diffs(retro_dir: str) -> None`
*   **Parameter:**
    *   `retro_dir`: The path to the retro directory (e.g., `retros/handterm`).
*   **Functionality:**
    *   Construct the full path to the `commits.log` file (e.g., `retros/handterm/commits.log`).
    *   Read the commit hashes from the `commits.log` file, line by line.
    *   Handle the case where `commits.log` is empty.
    *   Iterate through the commit hashes, keeping track of the *previous* commit hash.
    *   For each commit hash (except the first), call the `generate_diff` helper function to generate the diff file. Pass the appropriate commit hashes and the output path. The output path should be within the `diffs` subdirectory, in a folder named after the *current* commit hash, and use the naming convention described above: `retros/<retro_name>/diffs/<current_commit_hash>/<previous_commit_hash>_<current_commit_hash>.diff`.
    *   Handle any exceptions raised by `generate_diff`.

## Mermaid Diagram

```mermaid
graph LR
    A[Start] --> B{Read commits.log};
    B --> C{Empty commits.log?};
    C -- Yes --> D[End];
    C -- No --> E[Get first commit];
    E --> F[Loop through remaining commits];
    F --> G[Get current commit];
    G --> H[Create diff directory for current commit];
    H --> I[Generate diff (previous vs current)];
    I --> J[Save diff file in commit-specific folder];
    J --> F;
    F -- No more commits --> D;
```

## GitHub Issue

A GitHub issue (#12) has been created to track this feature request: [Feature: Generate diff files for each commit](https://github.com/bizkite-co/git-retrospector/issues/12)
