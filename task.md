# Task: Fix TestRunner Subscriptable Error

**Objective:** Resolve the runtime error `'TestRunner' object is not subscriptable` by correcting attribute access in `commit_processor.py` and `retro.py`.

**Context:**
*   A runtime error occurs because code attempts to access attributes of `TestRunner` Pydantic model instances using dictionary-style square brackets (`[]`) instead of object-style dot notation (`.`).
*   This error occurs in both `commit_processor.py` and the `run_tests` method within `retro.py`.

**Detailed Steps:**

1.  **Modify `src/git_retrospector/commit_processor.py`:**
    *   In the loop starting around line 45:
        *   Change `test_runner['name']` (line 46) to `test_runner.name`.
        *   Change `test_runner["output_dir"]` (line 50) to `test_runner.output_dir`.

2.  **Modify `src/git_retrospector/retro.py`:**
    *   Within the `run_tests` method (starting around line 240):
        *   Change `test_runner["command"]` (line 241) to `test_runner.command`.
        *   Change `test_runner['name']` (line 242) to `test_runner.name`.
        *   Change `test_runner['name']` (line 243) to `test_runner.name`.
        *   Change `test_runner['name']` (line 267) to `test_runner.name`.

3.  **Testing:**
    *   After applying the fixes, run the test suite (`python -m unittest discover tests` or equivalent) to ensure no regressions were introduced.
    *   Consider if a specific test case simulating the original error condition should be added to `tests/test_process_commit.py` or `tests/test_retro.py` to prevent this specific issue from recurring. This might involve mocking `retro.test_runners` with `TestRunner` objects and asserting that `retro.run_tests` and `commit_processor.process_commit` execute without the `TypeError`.
    *   Run the command that previously caused the error (`retrospector run <your_target_name> -i <iterations>`) to confirm the fix works in a real scenario.
