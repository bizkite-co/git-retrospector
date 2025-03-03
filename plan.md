# Plan to Resolve Test Output Copying Issue and Refactor

## Problem

The test output from remote retro runs is not being handled correctly. The output should be redirected to the appropriate XML files within the remote repository's `test-results` directory, but it's appearing in the console output of `git-retrospector`. Additionally, the `retros/handterm/` directory was being deleted, and the test setup was relying on temporary directories in a way that caused problems. Finally, the code was not as modular and configurable as it could be.

## Proposed Solution

1.  **Correct the Test Output Redirection (High Priority):**

    *   **Modify `runners.py`:**
        *   In `run_vitest`, remove the `--outputFile` argument. Vitest should use its internal configuration to determine the output file.
        *   In `run_playwright`, remove the `--output` argument. Playwright should use its internal configuration.
        *   In both functions, remove `capture_output=True`. This will allow the test output to be handled by the test runners' internal configuration.

        ```python
        # runners.py (modified)
        def run_vitest(target_repo, output_dir, retro):
            """Runs vitest tests."""
            command = [
                "npm",
                "run",
                "test",
                "--",
                "--run",
                "--reporter=junit",
            ]
            try:
                logging.info(f"Running vitest with command: {command}")
                retro.change_to_repo_dir() # Change to repo dir
                subprocess.run(command, check=True, text=True) # Removed capture_output

            except subprocess.CalledProcessError as e:
                logging.error(f"Error running vitest: {e}")
                logging.error(f"stdout: {e.stdout}")
                logging.error(f"stderr: {e.stderr}")
                raise e
            finally:
                retro.restore_cwd() # Restore original CWD


        def run_playwright(target_repo, output_dir, retro):
            """Runs playwright tests."""
            command = [
                "npx",
                "playwright",
                "test",
                "--reporter=junit",
            ]

            try:
                logging.info(f"Running playwright with command: {command}")
                retro.change_to_repo_dir() # Change to repo dir
                subprocess.run(
                    command, cwd=target_repo, check=True, text=True # Removed capture_output
                )
                logging.info(f"Playwright output: {result.stdout}")

            except subprocess.CalledProcessError as e:
                logging.error(f"Error running playwright: {e}")
                logging.error(f"stdout: {e.stdout}")
                logging.error(f"stderr: {e.stderr}")
                raise e
            finally:
                retro.restore_cwd() # Restore original CWD
        ```

    *   **Modify `commit_processor.py`:**
        *   Remove the logic that moves files from `test-results`.

        ```python
        # commit_processor.py (modified)
        # Remove this entire block:
        # try:
        #     source_dir = Path(target_repo) / "test-results"
        #     logging.info(
        #         f"Checking for existence of test-results directory: {source_dir}"
        #     )
        #     if source_dir.exists():
        #         logging.info(
        #             f"Moving test results from {source_dir} to "
        #             f"{retro.get_test_output_dir(commit_hash)}"
        #         )
        #         retro.move_test_results(commit_hash)
        #
        #     # Rename playwright.log to playwright.xml (now in the correct location)
        #     playwright_log_path = retro.get_playwright_log_path(commit_hash)
        #     logging.info(f"playwright_log_path: {playwright_log_path}")
        #     if playwright_log_path.exists():
        #         logging.info(f"Renaming {playwright_log_path} to playwright.xml")
        #         retro.rename_file(str(playwright_log_path), "playwright.xml")
        #
        # except Exception as e:
        #     logging.error(f"Error moving files: {e}")
        ```

2.  **Refactor `Retro` class (High Priority):**

    *   Add `change_to_repo_dir()` and `restore_cwd()` methods to manage the current working directory.
    *   Store the original CWD in the `Retro` constructor.
    *   Add a `run_tests` method that takes the test type (e.g., "vitest", "playwright") as an argument. This method will:
        *   Construct the appropriate command based on the test type.
        *   Use `subprocess.run` to execute the test command, redirecting `stdout` and `stderr` to a log file in the `retros/<name>/test-output/<commit_hash>/tool-summary` directory.
    * Add an `init_repo` method to initialize a git repo in the `repo_under_test_path`.

    ```python
    # retro.py (modified)
        def change_to_repo_dir(self):
            """Changes the current working directory to the target repo."""
            logging.info(f"Changing CWD to: {self.repo_under_test_path}")
            os.chdir(self.repo_under_test_path)


        def restore_cwd(self):
            """Restores the current working directory to the original value."""
            logging.info(f"Restoring CWD to: {self.original_cwd}")
            os.chdir(self.original_cwd)


        def run_tests(self, test_type, commit_hash):
            """Runs tests of the specified type."""
            if test_type == "vitest":
                command = [
                    "npm",
                    "run",
                    "test",
                    "--",
                    "--run",
                    "--reporter=junit",
                ]
            elif test_type == "playwright":
                command = [
                    "npx",
                    "playwright",
                    "test",
                    "--reporter=junit",
                ]
            else:
                raise ValueError(f"Unknown test type: {test_type}")

            try:
                logging.info(f"Running {test_type} with command: {command}")
                self.change_to_repo_dir()
                # Use relative path for output file, and redirect stdout/stderr
                log_file_path = (
                    self.get_test_output_dir(commit_hash) / f"{test_type}.log"
                )
                with open(log_file_path, "w") as outfile:
                    subprocess.run(command, check=True, stdout=outfile, stderr=subprocess.STDOUT, text=True, cwd=self.repo_under_test_path)

            except subprocess.CalledProcessError as e:
                logging.error(f"Error running {test_type}: {e}")
                logging.error(f"stdout: {e.stdout}")
                logging.error(f"stderr: {e.stderr}")
                raise e
            finally:
                self.restore_cwd()
                if test_type == "playwright":
                    # Unset the environment variable
                    if 'PLAYWRIGHT_JUNIT_OUTPUT_NAME' in os.environ:
                        del os.environ['PLAYWRIGHT_JUNIT_OUTPUT_NAME']

        def init_repo(self):
            """Initializes a git repository in the repo_under_test_path."""
            subprocess.run(["git", "init"], cwd=self.repo_under_test_path, check=True, capture_output=True, text=True)

    ```

3.  **Modify `tests/test_retro.py`:**

    *   Remove the `test_move_test_results` test. This test is no longer relevant as the logic for moving/copying files has changed. The test runners are now expected to write their output directly to the correct location within the remote repository's `test-results` directory, and the `Retro` class handles moving this entire directory to the local `retros` directory.
    *   Revert to using `tempfile.mkdtemp()` in the `setUp` method to create a temporary directory for each test run. This ensures proper isolation between tests.
    *   Set `repo_under_test_path` to a `test_repo` directory *within* the temporary directory created by `tempfile.mkdtemp()`.
    *   Remove the `original_cwd` attribute and the `os.chdir` calls from the test methods, as the CWD is now managed by the `Retro` class.
    *   In `tearDown`, remove the temporary directory created by `tempfile.mkdtemp()`.
    *   Remove the line `shutil.rmtree("retros", ignore_errors=True)` from the `tearDown` method. The tests should not modify anything outside of their temporary directory.
    * Call `retro.init_repo()` in the `setUp` method.

4. **Modify all other test files:**
    * Remove inheritance from `BaseTest`.
    * Remove import of `TestConfig`.
    * Add a `setUp` method that creates a temporary directory and initializes a `Retro` object.
    * Add a `tearDown` method that removes the temporary directory.

5.  **Add Mermaid Diagram to `README.md` (Medium Priority):**

    *   Create a Mermaid diagram illustrating the workflow:

    ```mermaid
    graph TD
        A[User runs git-retrospector] --> B(Clone/Checkout Remote Repo);
        B --> C{Iterate through Commits};
        C --> D[Checkout Commit];
        D --> E[Run Tests (Vitest/Playwright)];
        E --> F(Test Output to Remote Repo's test-results/);
        F --> G[Move Test Results to Local Retro Directory];
        G --> H{Next Commit?};
        H -- Yes --> C;
        H -- No --> I[Analyze Results];
        I --> J[Generate Reports/Create Issues];
    ```

    *   Add this diagram to `README.md`.

6.  **Add Link/Content to `README.md` (Medium Priority):**

    *   Embed the content of `docs/retro-tree-structure.md` into `README.md`.

7.  **Switch to Code Mode:**
    *   Implement the changes.
