# Plan to Resolve Test Output Copying Issue and Update README

## Problem

The test output from remote retro runs is not being copied to the local `retros/<remote_name>/test-output/<commit_hash>` directory as expected. The test runners (`vitest` and `playwright`) are being called with incorrect output paths, overriding the configuration within the remote repository and preventing the correct generation of JUnit XML reports. The standard output of the test runners is also being suppressed.

## Proposed Solution

1.  **Correct the Test Output Redirection (High Priority):**

    *   **Modify `runners.py`:**
        *   In `run_vitest`, remove the `--outputFile` argument.  Vitest should use its internal configuration to determine the output file.
        *   In `run_playwright`, remove the `--output` argument. Playwright should use its internal configuration.
        *   In both functions, remove `capture_output=True`.  This will allow the test output to be handled by the test runners' internal configuration.

        ```python
        def run_vitest(target_repo, output_dir, retro):
            """Runs vitest tests."""
            command = [
                "npm",
                "run",
                "test",
                "--",
                "--run",
            ]
            try:
                # Explicitly change directory
                logging.info(f"Running vitest with command: {command}")
                original_cwd = os.getcwd()
                logging.info(f"Original cwd: {original_cwd}")
                os.chdir(target_repo)
                logging.info(f"Changed cwd to: {os.getcwd()}")
                subprocess.run(command, check=True, text=True) # Removed capture_output

            except subprocess.CalledProcessError as e:
                logging.error(f"Error running vitest: {e}")
                logging.error(f"stdout: {e.stdout}")
                logging.error(f"stderr: {e.stderr}")
                raise e
            finally:
                # Change back to the original directory
                logging.info(f"Changing cwd back to: {original_cwd}")
                os.chdir(original_cwd)

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
                result = subprocess.run(
                    command, cwd=target_repo, check=True, text=True # Removed capture_output
                )
                logging.info(f"Playwright output: {result.stdout}")

            except subprocess.CalledProcessError as e:
                logging.error(f"Error running playwright: {e}")
                logging.error(f"stdout: {e.stdout}")
                logging.error(f"stderr: {e.stderr}")
                raise e
        ```

    *   **Modify `commit_processor.py`:**
        *   Remove the renaming of `playwright.log` to `playwright.xml`. The test runner should handle the correct naming.

        ```python
        # Remove this section:
        # # Rename playwright.log to playwright.xml (now in the correct location)
        # playwright_log_path = retro.get_playwright_log_path(commit_hash)
        # logging.info(f"playwright_log_path: {playwright_log_path}")
        # if playwright_log_path.exists():
        #     logging.info(f"Renaming {playwright_log_path} to playwright.xml")
        #     retro.rename_file(str(playwright_log_path), "playwright.xml")
        ```

2.  **Add Mermaid Diagram to `README.md` (Medium Priority):**

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

3.  **Add Link/Content to `README.md` (Medium Priority):**

    *   Embed the content of `docs/retro-tree-structure.md` into `README.md`.

4.  **Modify `retro.py`:**
    *   Change the `move_test_results` function to use `shutil.move` instead of `shutil.copytree`.
    *   Remove the destination directory if it exists before moving.
    *   Add logging statements.

5.  **Modify `tests/test_retro.py`:**
    *   Update the `test_move_test_results` test.

6.  **Modify `tests/test_retrospector_cli.py`:**
    *   Update the `test_init_command` to explicitly create the retro config file.

7.  **Switch to Code Mode:**
    *   Implement the changes.
