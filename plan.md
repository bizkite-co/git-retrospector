# Plan to Implement Issue Creation for Failed Tests

This plan outlines the steps to implement the functionality to create GitHub issues for failed tests from a specific commit.

## Steps

1.  **Add `issues` subcommand:**
    *   Modify `src/git_retrospector/retrospector.py` to include a new subcommand named `issues`.
    *   This subcommand should accept two arguments:
        *   `retro_name`: The name of the retro (e.g., "handterm").
        *   `commit_hash`: The hash of the commit to analyze.

2.  **Directory check:**
    *   Implement logic within the `issues` subcommand to check if the commit directory exists.
    *   The commit directory path will be `retros/{retro_name}/test-output/{commit_hash}`.
    *   Use `os.path.exists` to check for the directory's existence.

3.  **CSV reading:**
    *   Implement logic to read the `playwright.csv` and `vitest.csv` files.
    *   These files will be located in a subdirectory named `tool-summary` within the commit directory: `retros/{retro_name}/test-output/{commit_hash}/tool-summary/`.
    * Use a function to locate these files.

4.  **Count failures:**
    *   Parse the CSV files and count the number of failed tests in each file.
    *   Store these counts for display to the user.

5.  **User prompt:**
    *   Display the total number of failed tests (and thus the number of issues to be created) to the user.
    *   Prompt the user to confirm if they want to proceed with creating the GitHub issues.
    *   Use a simple "yes/no" prompt.

6.  **GitHub issue creation:**
    *   If the user confirms, iterate through the failed tests in the CSV files.
    *   For each failed test, create a GitHub issue using the **PyGithub** library.
        *   **Title:** The name of the failed test.
        *   **Body:** Include the error description (if any), the stack trace (if available), and a link to the screenshot (if available).
    *   Use the `Github` class and its methods to authenticate and create issues.

7.  **Modify `process_commit`:**
    *   Modify the `process_commit` function in `src/git_retrospector/commit_processor.py`.
    *   Change the logic to create a `tool-summary` subdirectory within the commit's output directory.
    *   Move the `playwright.csv` and `vitest.csv` files into this `tool-summary` directory.

## Implementation Notes

*   The **PyGithub** library should be used for creating issues.
*   Authenticate with GitHub using a personal access token (PAT) stored in the `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable.
*   Error handling should be implemented to gracefully handle cases like missing files, invalid CSV formats, or GitHub API errors.
