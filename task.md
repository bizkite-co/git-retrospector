# Task: Refactor Commit Selection (Phase 1)

**Objective:** Implement the first phase of the refactoring plan outlined in `plan.md`. This involves changing how commits are selected based on an iteration count and storing the results in a new JSON manifest file.

**Detailed Steps:**

1.  **Modify `src/git_retrospector/git_utils.py`:**
    *   Add a new function `get_commit_list(repo_path: str, num_commits: int) -> list[dict]`.
    *   Inside the function:
        *   Construct the `git log` command: `['git', 'log', f"--pretty=format:%H|%ad|%s", '--date=iso', f'-n{num_commits}']`.
        *   Use `subprocess.run` to execute the command in the `repo_path` directory, capturing the output (`stdout`). Remember to handle potential errors (e.g., using `check=True` and a `try...except` block).
        *   Process the `stdout`:
            *   Decode it to a string.
            *   Split the string into lines.
            *   For each line, split it by the '|' delimiter.
            *   Create a dictionary for each commit: `{'hash': parts[0], 'date': parts[1], 'summary': parts[2]}`.
            *   Handle potential errors during parsing (e.g., if a line doesn't have 3 parts).
        *   Return the list of commit dictionaries.
    *   Ensure necessary imports are present (e.g., `subprocess`, `logging`).

2.  **Refactor `src/git_retrospector/retrospector.py` (within the `run_tests` function):**
    *   **Remove:** Delete the `for i in range(iteration_count):` loop (approximately lines 167-189) which contains the `git rev-parse` logic and the call to `process_single_commit` inside the loop. Also remove the `commits_log.write(f"{commit_hash}\n")` line within that loop.
    *   **Add (before where the loop was):**
        *   Import `get_commit_list` from `.git_utils`.
        *   Import `json`.
        *   Call the new function: `commit_list = get_commit_list(target_repo, iteration_count)` (handle potential exceptions).
        *   Define the manifest file path: `manifest_path = Path(retro.get_test_output_dir()) / "commit_manifest.json"`.
        *   Write the `commit_list` to the `manifest_path` using `json.dump()`:
            ```python
            try:
                manifest_path.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
                with open(manifest_path, 'w') as f:
                    json.dump(commit_list, f, indent=2)
                logging.info(f"Commit manifest written to {manifest_path}")
            except Exception as e:
                logging.error(f"Failed to write commit manifest: {e}")
            ```
    *   **Add (replace the old loop):**
        *   Create a new loop: `for commit_info in commit_list:`.
        *   Inside this new loop, extract the hash: `commit_hash = commit_info['hash']`.
        *   Call `process_single_commit` using this `commit_hash`:
            ```python
            process_single_commit(
                target_repo, commit_hash, test_output_dir, origin_branch, retro
            )
            ```
    *   **Remove:** Delete the `commits_log_path` definition and the `with open(commits_log_path, "w") as commits_log:` block (around lines 148-150).

**Reference:** Consult `plan.md` for the overall context and diagrams.
