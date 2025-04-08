import logging
import os
import subprocess
import time

from git_retrospector.retro import Retro  # Use new class name


def process_commit(
    remote_repo_path, commit_hash, test_output_dir, origin_branch, retro: Retro
):
    """
    Processes a single commit: checks it out, runs tests, and moves results.

    Args:
        remote_repo_path (str): Path to the target repository.
        commit_hash (str): The commit hash to process.
        test_output_dir (str): The base directory for test outputs.
        origin_branch (str): The original branch to return to.
        retro (Retro): The configuration object.
    """
    logging.info(f"process_commit called with hash: {commit_hash}")

    try:
        # Checkout the specific commit
        subprocess.run(
            ["git", "checkout", commit_hash],
            cwd=remote_repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        logging.info(f"Checked out commit: {commit_hash}")

        # --- Debugging log added here ---
        logging.info(f"Type of 'retro' object in process_commit: {type(retro)}")
        # logging.info(f"Attributes of 'retro' object: {dir(retro)}")
        # Keep commented out for now
        # --- End of debugging log ---

        # Create directories for the commit hash using the correct method name
        retro.create_output_dirs(commit_hash)  # Corrected method call
        # commit_hash_dir, tool_summary_dir = retro.create_commit_hash_dir(commit_hash)

        # Run configured test runners
        for test_runner in retro.test_runners:
            logging.info(
                f"Running test runner: {test_runner.name}"
            )  # Changed to dot notation
            retro.run_tests(test_runner, commit_hash)
            # Move results after each runner finishes
            retro.move_test_results_to_local(
                commit_hash, test_runner.output_dir  # Changed to dot notation
            )

        # Optional delay and sync
        time.sleep(1)
        os.sync()

    except subprocess.CalledProcessError as e:
        logging.error(
            f"Error during git checkout or test execution for {commit_hash}: {e}"
        )
        logging.error(f"Stderr: {e.stderr}")
    except Exception as e:
        logging.error(f"Unexpected error processing commit {commit_hash}: {e}")
    finally:
        # Ensure we always attempt to switch back to the original branch
        try:
            subprocess.run(
                ["git", "checkout", "--force", origin_branch],
                cwd=remote_repo_path,
                check=True,  # Check if switching back succeeds
                capture_output=True,
                text=True,
            )
            logging.info(f"Switched back to branch: {origin_branch}")
        except subprocess.CalledProcessError as e:
            logging.error(
                f"CRITICAL: Failed to switch back to original branch {origin_branch}"
                f""" after processing {
                    commit_hash
                }. Manual intervention may be needed. Error: {e}"""
            )
