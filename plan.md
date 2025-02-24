# Unit Test Plan for git-retrospector

This plan outlines the unit tests to be written for the `git-retrospector` project, specifically focusing on the functions related to target-specific output directories and test execution.

## Goals

*   Verify that the `initialize` function correctly creates the directory structure and `config.toml` file.
*   Verify that `run_tests` correctly loads the configuration and determines the target repository and output directory.
*   Verify that `process_commit` correctly constructs the commit-specific output directory.
*   Verify that `run_vitest` and `run_playwright` construct the correct test commands and output file paths.
*   Ensure that no files are written to the target repository itself.
*   Ensure that tests are using mocked subprocess calls to avoid actual test execution during unit testing.

## Test Cases

### 1. `initialize`

*   **test\_initialize\_creates_directory\_and_config:**
    *   Call `initialize` with a test target name and source directory.
    *   Assert that the target directory (`retros/[target_name]`) is created.
    *   Assert that the `config.toml` file is created within the target directory.
    *   Assert that the `config.toml` file contains the correct keys (`name`, `source_dir`, `test_result_dir`, `output_paths`, `test_output_dir`).
    *   Assert that the values in `config.toml` match the input values and expected defaults.

### 2. `run_tests`

*   **test\_run\_tests\_loads_config:**
    *   Create a temporary directory and a mock `config.toml` file within it.
    *   Call `run_tests` with a test target name and iteration count.
    *   Assert that `run_tests` correctly loads the `target_repo` and `test_output_dir` values from the mock `config.toml`.
* **test_run_tests_handles_missing_config:**
    *   Call `run_tests` with a target that does not have a config file.
    *   Assert that `run_tests` handles the error gracefully (prints an error message and returns).
* **test_run_tests_checks_target_repo:**
    *   Call `run_tests` with a target name, but make the `get_current_commit_hash` function (which is used to check if it is a git repo) return None.
    *   Assert that `run_tests` handles the error and returns.

### 3. `process_commit`

*   **test\_process\_commit\_creates_output\_dir:**
    *   Call `process_commit` with a test target repo, commit hash, output dir, and origin branch.
    *   Assert that the commit-specific output directory is created correctly.
*   **test\_process\_commit\_loads_config:**
    *   Create a mock `config.toml` file.
    *   Call `process_commit`.
    *   Assert that `process_commit` correctly loads the `test_output_dir` value from the mock `config.toml`.
*   **test\_process_commit\_calls_run_tests:**
     *  Mock `run_vitest` and `run_playwright`.
     *  Call `process_commit`.
     *  Assert that `run_vitest` and `run_playwright` are called with the correct arguments (target repo and commit-specific output directory).

### 4. `run_vitest` and `run_playwright`

*   **test\_run\_vitest\_constructs_command:**
    *   Call `run_vitest` with a test target repo and output directory.
    *   Mock `subprocess.run`.
    *   Assert that `subprocess.run` is called with the correct arguments:
        *   `cwd` should be the current working directory.
        *   `--outputFile` should point to the correct commit-specific output path within the `retros` directory structure, *not* within the target repository.
*   **test\_run\_playwright\_constructs\_command:**
    *   Call `run_playwright` with a test target repo and output directory.
    *   Mock `subprocess.run`.
    *   Assert that `subprocess.run` is called with the correct arguments:
        *   `cwd` should be the current working directory.
        *   `PLAYWRIGHT_JUNIT_OUTPUT_NAME` environment variable should be set correctly, pointing to a commit-specific path within the `retros` directory structure.

## Mocking

The `subprocess.run` function will be mocked using `unittest.mock` (or a similar library) to prevent actual test execution and to allow us to assert that it's called with the correct arguments.

## Implementation

The tests will be implemented in `tests/test_retrospector.py`, extending the existing `TestRetrospector` class.