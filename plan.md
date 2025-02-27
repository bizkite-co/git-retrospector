# Plan to Address Issue #18: Convert print statements to logging

## Goal

Migrate all `print` statements in the `src/` directory to use the `logging` library, optimizing for performance and clarity. Differentiate between debug/informational messages and user-facing output (tagging the latter with `# TODO: Convert to CLI`).

## Steps

1.  **Identify `print` statements:** Use `search_files` to locate all instances of `print(` within the `src/` directory.
2.  **Analyze context:** Examine each `print` statement and its surrounding code to determine the appropriate logging level (debug, info, warning, error).
3.  **Replace with `logging` calls:** Use `apply_diff` to replace `print` statements with corresponding `logging` calls.
    *   Use `logging.debug()` for detailed debugging information.
    *   Use `logging.info()` for general informational messages.
    *   Use `logging.warning()` for potential issues.
    *   Use `logging.error()` for error messages.
    *   Add `# TODO: Convert to CLI` to `print` statements that seem to be intended for user interaction.
4.  **Review logging configuration:** Ensure the existing logging configuration in `src/git_retrospector/retrospector.py` is appropriate.
5.  **Run tests:** Execute the test suite (`tests/`) to verify that the changes haven't introduced any regressions.
6.  **Commit changes:** Commit the changes with a descriptive message, referencing issue #18.
7.  **Update issue (on GitHub):** Add a comment to issue #18, summarizing the changes and marking it as ready for review/testing.

## Detailed Changes

The following changes will be made using `apply_diff` (file paths are relative to the project root):

**src/git_retrospector/diff_generator.py:**

*   Change 1:
    ```diff
    <<<<<<< SEARCH
            print(f"Error: Could not load config from {config_file_path}")  # noqa T201
            return
    =======
            logging.error(f"Error: Could not load config from {config_file_path}")
            return
    >>>>>>> REPLACE
    ```

*   Change 2:
    ```diff
    <<<<<<< SEARCH
                    print(  # noqa: T201
                        f"repo_path: {repo_path}, commit1: {previous_commit}, "
                except Exception as e:
    =======
                    logging.debug(
                        f"repo_path: {repo_path}, commit1: {previous_commit}, "
                    )
                except Exception as e:
    >>>>>>> REPLACE
    ```

*   Change 3:
    ```diff
    <<<<<<< SEARCH
                    print(  # noqa: T201
                        f"Error: diff for {previous_commit} -> {current_commit}: {e}"
    =======
                    logging.error(
                        f"Error: diff for {previous_commit} -> {current_commit}: {e}"
                    )
    >>>>>>> REPLACE
    ```

**src/git_retrospector/retrospector.py:**

*   Change 1:
    ```diff
    <<<<<<< SEARCH
            print(  # noqa: T201
                f"Error: Config file not found: {config_file_path}\n"
        if not should_create_issues(retro_name, commit_hash):
    =======
            print(  # noqa: T201, TODO: Convert to CLI
                f"Error: Config file not found: {config_file_path}\n"
                f"Please run: './retrospector.py init {target_name} <target_repo_path>'"
            )
            logging.error(f"Config file not found: {config_file_path}")
        if not should_create_issues(retro_name, commit_hash):
    >>>>>>> REPLACE
    ```
* Change 2:
    ```diff
    <<<<<<< SEARCH
            print("should_create_issues returned False")  # noqa: T201
            return
        if not repo_owner or not repo_name:
    =======
            logging.info("should_create_issues returned False")  # TODO: Convert to CLI
            return
        if not repo_owner or not repo_name:
    >>>>>>> REPLACE
    ```

*   Change 3:
    ```diff
    <<<<<<< SEARCH
            print("Could not load repo owner or name")  # noqa: T201
            return
    =======
            logging.info("Could not load repo owner or name")  # TODO: Convert to CLI
            return
    >>>>>>> REPLACE
    ```

**src/git_retrospector/config.py:**

*No changes needed (already commented out).*

**src/git_retrospector/runners.py:**

*No changes needed (already commented out).*

**src/git_retrospector/parser.py:**

*   Change 1 (already commented out, no change needed)
*   Change 2 (already commented out, no change needed)

*   Change 3:
    ```diff
    <<<<<<< SEARCH
        print(f"Processing Playwright XML: {playwright_xml_path}")  # noqa: T201
        try:
                csv_output_path = os.path.join(tool_summary_dir, "playwright.csv")
    =======
        logging.info(f"Processing Playwright XML: {playwright_xml_path}")
        try:
                csv_output_path = os.path.join(tool_summary_dir, "playwright.csv")
    >>>>>>> REPLACE
    ```

*   Change 4:
    ```diff
    <<<<<<< SEARCH
                print(f"Writing Playwright CSV to: {csv_output_path}")  # noqa: T201
                with open(csv_output_path, "w", newline="") as individual_csvfile:
    =======
                logging.info(f"Writing Playwright CSV to: {csv_output_path}")
                with open(csv_output_path, "w", newline="") as individual_csvfile:
    >>>>>>> REPLACE
    ```

**src/git_retrospector/git_utils.py:**

*   Change 1:
    ```diff
    <<<<<<< SEARCH
            print(f"Error getting original branch: {e}", file=sys.stderr)  # noqa T201
            return None
        except subprocess.CalledProcessError as e:
    =======
            logging.error(f"Error getting original branch: {e}")
            return None
        except subprocess.CalledProcessError as e:
    >>>>>>> REPLACE
    ```
* Change 2:
    ```diff
    <<<<<<< SEARCH
            print(f"Error getting current commit hash: {e}", file=sys.stderr)  # noqa T201
            return None
        except subprocess.CalledProcessError:
    =======
            logging.error(f"Error getting current commit hash: {e}")
            return None
        except subprocess.CalledProcessError:
    >>>>>>> REPLACE
    ```
* Change 3 (already commented out, no change needed)
