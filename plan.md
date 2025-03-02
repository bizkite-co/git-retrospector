# Git Retrospector Improvement Plan: Issue #7 (Revised)

This plan addresses the remaining work for GitHub Issue #7 (Create Issue for Failed Tests with Media) in the bizkite-co/git-retrospector repository, taking into account the feedback and difficulties encountered during implementation.

## Goals

1.  **Fix Failing Test:** Correct the `test_parse_playwright_xml` test in `tests/test_xml_processor.py` and ensure the `parse_playwright_xml` function in `src/git_retrospector/xml_processor.py` correctly handles media paths. Simplify the test to focus on core functionality.
2.  **Implement `process-results` Command:** Add a new command-line command to `retrospector.py` that allows processing of existing XML test results without re-running the tests.
3.  **Integrate Screenshot Upload (Issue #7 Core):** Integrate the screenshot upload functionality into the issue creation process.
4.  **Address Config File Deletion:** Prevent the test suite from deleting the `retros/handterm/config.toml` file.
5. **Verify and Add Unit Tests:** Add new unit tests and run all tests to ensure everything works as expected and no regressions were introduced.
6. **Refactor:** Look for opportunities to refactor and simplify the code, including using a JSON file for test data if appropriate.

## Detailed Steps

### 1. Fix Failing Test (`test_parse_playwright_xml`)

*   **Switch to Code Mode:**
*   **Modify `tests/test_xml_processor.py`:**
    *   Remove the `test_parse_playwright_xml_handterm` method.
    *   In `test_parse_playwright_xml`:
        *   Revert the change from "media_path" back to "screenshot_path" in the `expected_result`.
        *   Simplify the `xml_content` to include only necessary test cases (e.g., a test case with a screenshot, a test case without a screenshot, and potentially a test case with an invalid path).
        *   Update the `expected_result` to match the simplified `xml_content`, using relative paths and the `os.getcwd()` for constructing the expected absolute paths.
    *   Ensure there are no syntax errors (missing closing braces/brackets).
    *   Address line length issues.
* **Create `tests/fixtures/playwright_results.json` (Later):** After the basic test is working, consider moving the test data to a JSON file for better organization.
* **Run Tests:** After making these changes, run the tests to ensure they pass.

### 2. Implement `process-results` Command

*   **Add CLI Command (in `src/git_retrospector/retrospector.py`):**
    *   Add `@cli.command("process-results")` above a new function named `process_results_command`.
    *   Use `@click.argument("path", type=click.Path(exists=True))` to accept a path (file or directory) as input.
    *   Call a helper function (e.g., `process_xml_results(path)`) to handle the processing.
*   **Create `process_xml_results(path)` (in `src/git_retrospector/retrospector.py`):**
    *   Check if `path` is a file or directory using `os.path.isfile()` and `os.path.isdir()`.
    *   **If `path` is a file:**
        *   Read the file content.
        *   Call `process_xml_string` (from `xml_processor.py`) to process the XML.
    *   **If `path` is a directory:**
        *   Use `os.walk()` or `glob.glob()` to find all `.xml` files.
        *   For each XML file:
            *   Read the file content.
            *   Call `process_xml_string`.
*  **Add to `handle_no_command`:** Add "process-results" to the `WordCompleter` in the `handle_no_command` function, and add a clause to the `if/elif/else` block to call `process_results_command` when the user types "process-results".

### 3. Integrate Screenshot Upload (Issue #7 Core)

*   **Review Existing Code:** Examine `src/git_retrospector/retrospector.py` and related files (especially `commit_processor.py` and potentially `parser.py`) to understand how failed tests are currently handled and where issue creation logic resides.
*   **Modify Issue Creation:**  Locate the code that creates GitHub issues (likely within `create_github_issues` or a similar function).
    *   Modify this code to:
        *   Check if a `media_path` key exists and is not empty in the data for a failed test.
        *   If `media_path` exists, split it by semicolons to get individual file paths.
        *   For each file path:
            *   Check if the file exists.
            *   If it exists and is an image (check extension, e.g., `.png`, `.jpg`), call `upload_screenshot_to_github` to upload it.
            *   Include the returned URL in the GitHub issue body (using Markdown image syntax: `![alt text](url)`).
        * If it exists and is a video, include the path in the GitHub issue body.
        * If it exists and is a trace, include the path in the GitHub issue body.

### 4. Address Config File Deletion

*   **Examine Test Suite:**  Investigate the test suite setup and teardown logic, likely in `tests/test_retrospector.py` or a common test configuration file.
*   **Identify Deletion:** Find where `retros/handterm/config.toml` is being removed.
*   **Prevent Deletion:** Modify the test suite to either:
    *   Not delete the file.
    *   Copy the file to a temporary location before the tests and restore it afterward.
    *   Recreate the file if it's deleted.

### 5. Verify and Add Unit Tests

*   **Run All Tests:** After making changes, run all tests (`python -m unittest discover tests`) to ensure no regressions.
*   **Add Unit Tests:**
    *   Add new unit tests for `process_xml_results` in `tests/test_retrospector.py` (or a new test file).
    *   Test cases:
        *   Processing a single valid XML file.
        *   Processing a directory with multiple XML files.
        *   Processing a directory with no XML files.
        *   Processing an invalid XML file (should handle the error gracefully).
        *   Processing an XML file with no failed tests.
        *   Processing an XML file with failed tests and media.
    * Add new unit tests for `parse_playwright_xml` in `tests/test_xml_processor.py`
    *   Test cases:
        *   Processing an XML file with failed tests and media in `<system-out>`.
        *   Processing an XML file with no failed tests.
        *   Processing an XML file with failed tests and no media.

### 6. Refactor

* Look for opportunities to refactor the existing code to avoid duplication. For example, the logic for finding XML files might be shared between the `run` command and the new `process-results` command.

## GitHub Issue Update

I will update the body of Issue #7 with a summary of the completed work and the remaining tasks, referencing this plan.

## `retros` Directory Structure

The `retros` directory is the base directory for storing retrospective data for different target repositories.  Its structure is as follows:

```
retros/
├── <target_name_1>/       # Directory for a specific target (e.g., handterm, test_target)
│   ├── config.toml        # Configuration file for this target
│   └── test-output/       # Directory for test output
│       └── <commit_hash>/  # Directory for a specific commit
│           ├── playwright.xml # Playwright JUnit-schema test output
│           ├── vitest.xml # Vitest JUnit-schema test output
│           └── tool-summary/   # Summary of test results
│               ├── playwright.csv   # CSV file with Playwright test results
│               └── vitest.csv      # CSV file with Vitest test results (if applicable)
│           └── playwright.xml # Raw Playwright XML output
│           └── ...            # Other output files (screenshots, videos, traces)
├── <target_name_2>/       # Another target repository
│   ├── config.toml
│   └── test-output/
│       └── ...
└── ...
```

*   **`<target_name>`:**  This is the name of the target repository being analyzed (e.g., "handterm", "test_target").  It's specified when running the `init` command.
*   **`config.toml`:**  This file contains the configuration for a specific target, including the repository path, test result directory, and output paths for different testing tools.
*   **`test-output`:** This directory stores the output of test runs.
*   **`<commit_hash>`:**  A directory named after the short commit hash, containing the test results for that specific commit.
* **`tool-summary`**: Contains a summary of test results in CSV format.
*   **`playwright.csv`:**  A CSV file containing parsed Playwright test results.
*   **`vitest.csv`:** A CSV file containing parsed Vitest test results (if Vitest is used in the target project).
* **`playwright.xml`:** The raw XML output from Playwright.
*   **`...`:** Other files and directories might be present within the commit directory, such as screenshots, videos, and traces generated by Playwright.

The `Config.initialize` method is responsible for creating the `retros/<target_name>` directory and the `config.toml` file within it. The `run` command then creates the `test-output/<commit_hash>` directories and their contents when tests are executed for a specific commit.
