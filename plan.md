# Plan to Fix Failing Tests and Improve Error Handling

## Objective

Fix the failing `test_create_issues_for_commit_success` test in `tests/test_create_issues.py` and improve error handling in `src/git_retrospector/retrospector.py` to prevent silent failures.

## Current Issues

1.  **Silent Failure in `find_test_summary_files`:** The function returns `None, None` if the `tool-summary` directory or expected CSV files are not found. This leads to the test failing silently without clear indication of the root cause.
2.  **Incorrect Mocking:** The mocking strategy in `test_create_issues_for_commit_success` has been inconsistent, leading to the test not correctly simulating the intended behavior.
3.  **Lack of Explicit Error Handling:** The code doesn't explicitly handle potential errors like missing directories or files, making it harder to debug and maintain.
4. **Test waits for input:** The test gets stuck waiting for user input because of the call to the `input()` function.

## Proposed Solution

### 1. Improve Error Handling in `find_test_summary_files`

*   [ ] **Modify `find_test_summary_files`:**
    *   Instead of returning `None, None`, raise a `FileNotFoundError` with a descriptive message if the `tool-summary` directory or the expected CSV files (`playwright.csv`, `vitest.csv`) are not found.

### 2. Improve Error Handling in `should_create_issues`

*   [ ] **Modify `should_create_issues`:**
    *   Add a `try-except` block around the call to `find_test_summary_files`.
    *   Catch the `FileNotFoundError` and handle it appropriately (e.g., log an error message, return `False`).

### 3. Fix Mocking and Assertions in `test_create_issues_for_commit_success`

*   [ ] **Modify `test_create_issues_for_commit_success`:**
    *   Remove the `@patch("git_retrospector.retrospector.create_issues_for_commit")` decorator from all test methods.
    *   Add `@patch("git_retrospector.retrospector.create_github_issues")` to `test_create_issues_for_commit_success`.
    *   Inside the test, create a `mock_github = MagicMock()`.
    *   Set `mock_create_github_issues.return_value = mock_github`.
    *   Set `mock_github.get_user.return_value.get_repo.return_value = mock_repo`.
    *   Keep the existing test setup (creating the directory and CSV files).
    *   Keep the assertion that `mock_repo.create_issue.call_count` is 2.
    *   Keep the assertions that check the arguments passed to `create_issue`.
* [ ] Remove duplicate test.

### 4. Address the input() call

* [x] The `input()` call in `get_user_confirmation` is correctly mocked in the test using `@patch("git_retrospector.retrospector.input", return_value="y")`. The issue was that the test was failing *before* reaching that point. With the corrected mocking and error handling, this should no longer be a problem.

## Steps

1.  [ ] Modify `src/git_retrospector/retrospector.py`:
    *   Update `find_test_summary_files` to raise `FileNotFoundError`.
    *   Update `should_create_issues` to handle `FileNotFoundError`.
    *   Remove debugging print statements.
2.  [ ] Modify `tests/test_create_issues.py`:
    *   Adjust mocking in `test_create_issues_for_commit_success` as described above.
3.  [ ] Run tests and ensure they pass.

## Future Considerations (Beyond this immediate task)

*   **Ruff Configuration:** Review and configure Ruff to enforce stricter error checking and prevent similar issues.
*   **Type Hinting:** Add type hints throughout the codebase and use a type checker (like MyPy) to catch potential type errors.
*   **Code Reviews:** Emphasize error handling and test coverage during code reviews.
* **Review Issue #14:** Check if the issue on GitHub already covers the need for creating the `tool-summary` folder and add information if necessary.
