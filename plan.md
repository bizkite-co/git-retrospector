# Plan to Rename Repository to "git-retrospector"

## Goal

Rename the GitHub repository "git-test-retrospector" to "git-retrospector", and update all code references.

## Steps

1.  **Rename Repository on GitHub:**
    *   Use the `execute_command` tool to run `gh repo rename`.
    *   Current Repo Name: `git-test-retrospector`
    *   New Name: `git-retrospector`
    *   Full command: `gh repo rename bizkite-co/git-test-retrospector git-retrospector`

2.  **Update Code References:**
    *   Use `search_files` to find all instances of `git-test-retrospector`.
        *   Search in the root directory (`.`).
        *   Regex: `git-test-retrospector`
        *   File pattern: `*` (all files)
    *   For each file with matches:
        *   Use `apply_diff` to replace `git-test-retrospector` with `git-retrospector`.

3. **Update the open tab**
    *   Use `search_files` to find all instances of `src/git_test_retrospector/retrospector.py`.
    *   Search in the root directory (`.`).
    *   Regex: `src/git_test_retrospector/retrospector.py`
    *   Use `apply_diff` to replace `src/git_test_retrospector/retrospector.py` with `src/git-retrospector/retrospector.py`.

4.  **Update GitHub Issue #6 Status to "In Progress":**
    * Use the `github` MCP server's `update_issue` tool.
    *   Owner: `bizkite-co`
    *   Repo: `git-test-retrospector` (will need to be updated after renaming)
    *   Issue Number: `6`
    *   State: `open` (no specific "In Progress" state, so we'll leave it open)

5.  **Update GitHub Issue #6 Status to "Done":**
     * Use the `github` MCP server's `update_issue` tool.
    *   Owner: `bizkite-co`
    *   Repo: `git-retrospector` (after renaming)
    *   Issue Number: `6`
    *   State: `closed`