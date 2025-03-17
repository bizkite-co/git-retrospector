# Plan to Fix Failing Tests

1.  **Run Tests:** Use the command `uvx hatch run test` to execute the test suite. (This will be done in Code mode).
2.  **Analyze Test Results:**
    *   Capture the output of the test execution.
    *   Identify any failing tests, including the test name, file, and error message.
    *   Categorize the failures (e.g., assertion errors, exceptions).
3.  **Iterate Through Failures (One at a Time):** For each failing test:
    a. **Investigate Failure:**
        *   Read the relevant test code (`tests/` directory).
        *   Read the corresponding source code (`src/` directory) that the test is exercising.
        *   Analyze the code to understand the cause of the failure. This might involve:
            *   Examining the logic of the test and the code being tested.
            *   Looking for recent changes (using `git_log` or similar, if necessary).
            *   Identifying potential edge cases or boundary conditions that are not handled correctly.
    b. **Develop Fix:**
        *   Determine the necessary code changes to address the issue.
        *   Consider potential side effects of the changes.
        *   Ensure the fix adheres to the project's coding style and best practices (as outlined in `.clinerules`).
    c. **Implement Fix (Code Mode):**
        *   Modify the code in the `src/` directory to implement the fix.
        *   Add or modify unit tests in the `tests/` directory as needed to cover the corrected code and prevent regressions.
    d. **Re-run Tests:** After implementing the fix for a single test, re-run the tests using `uvx hatch run test` to ensure that the specific test passes and that no new failures have been introduced.
4.  **Address Linting Errors (If Any):** If all tests pass, address any linting errors reported by a linter (if configured). I'll need to check the project configuration (e.g., `pyproject.toml`, `.pre-commit-config.yaml`) to determine which linter is used.
5. **Create GitHub Issue:** Create a GitHub issue to track each bug fix, including the test output and a description of the fix.
6. **Commit Changes:** Commit the changes with a message that references the GitHub issue number, following the format specified in `.clinerules`.

**Mermaid Diagram (Conceptual):**

```mermaid
graph TD
    A[Start] --> B(Run Tests: uvx hatch run test);
    B --> C{Tests Pass?};
    C -- No --> D[Analyze Failures];
    D --> E[Iterate Through Failures];
    E --> F[Investigate: Read Test & Source Code];
    F --> G[Develop Fix];
    G --> H[Implement Fix (Code Mode)];
    H --> I[Re-run Tests];
    I --> J{Test Pass?};
    J -- Yes --> E;
    J -- No --> H;
    C -- Yes --> K[Address Linting Errors (If Any)];
    K --> L[Create GitHub Issue];
    L --> M[Commit Changes];
    M --> N[End];
