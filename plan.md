# Plan to Refactor Test Result Capture and Handling

This plan updates the original plan to reflect the current state of the project and the refined approach to refactoring the test result capture and handling in `git-retrospector`.

## Current Task

Implement the solution for issue #24, focusing on dynamic test runner configuration and proper test result handling.

## Refined Approach (Based on User Feedback)

The original plan involved specific steps, some of which are already implemented or need modification. The refined approach, based on user feedback, focuses on these key changes:

1.  **Modify `process_commit` in `src/git_retrospector/commit_processor.py`:**
    *   Instead of calling `run_tests` with hardcoded strings ("vitest", "playwright"), loop through the `test_runners` array from the `retro.toml` file.
    *   Pass the `test_runner` object to `run_tests` in each iteration.

2.  **Modify `run_tests` in `src/git_retrospector/retro.py`:**
    *   Update `run_tests` to accept a `test_runner` object as a parameter.
    *   Use the `command` from the `test_runner` object in the `subprocess.run` call.

3.  **Move and Modify `move_test_results_to_local`:**
    *   Move the call to `retro.move_test_results_to_local` inside the loop in `process_commit`.
    *   Add a parameter to `move_test_results_to_local` to accept the remote output directory.

4. **Modify `retro.toml`:** Add a `test_runners` array to the `retro.toml` file for the `handterm` configuration. This array will specify the commands to run for each test type, and the output directory.

    ```toml
    [[test_runners]]
    name = "vitest"
    command = "npm run test:vitest-log"
    output_dir = "vitest-output"

    [[test_runners]]
    name = "playwright"
    command = "npm run test:playwright-log"
    output_dir = "test-results"
    ```
5. **Modify `Retro` class:** Update `src/git_retrospector/retro.py` to include a `test_runners` field of type `list[dict]`.

## Detailed Steps

1.  **Read Files:** Read the contents of `src/git_retrospector/commit_processor.py`, `src/git_retrospector/retro.py`, and `retros/handterm/retro.toml`. (Done)
2.  **Modify `src/git_retrospector/retro.py`:** (Done)
    *   Update `run_tests` signature: `def run_tests(self, test_runner, commit_hash):`
    *   Update `run_tests` body to use `test_runner["command"].split()` for the `subprocess.run` command.
    *   Update `move_test_results_to_local` signature: `def move_test_results_to_local(self, commit_hash, output_dir):`
    *   Update `move_test_results_to_local` body to use the `output_dir` parameter when constructing the `remote` path.
    *   Add `test_runners` to `Retro` class: Add `test_runners: list[dict] = Field(default=[], exclude=True)` to the `Retro` class.
3.  **Modify `src/git_retrospector/commit_processor.py`:** (Done)
    *   Load the `retro.toml` file within `process_commit`.
    *   Loop through `retro.test_runners`.
    *   Call `retro.run_tests(test_runner, commit_hash)` inside the loop.
    *   Call `retro.move_test_results_to_local(commit_hash, test_runner["output_dir"])` inside the loop, *after* calling `run_tests`.
4. **Modify `retros/handterm/retro.toml`:** (Done) Add the `test_runners` array.
5. **Run tests:** (Done) Verify that the changes work as expected by running `hatch run test` and `hatch run handterm 1`.
6. **Inspect output:** (Current Step) Check that `retros/handterm/test-output/<commit_hash>` contains both `playwright.xml` and `vitest.log` for each commit processed by `hatch run handterm 1`.
7. **Investigate `handterm`'s `package.json`:** Read `/home/mstouffer/repos/handterm-proj/handterm/package.json` to understand how the `test:vitest-log` and `test:playwright-log` scripts are defined and where they output results.
