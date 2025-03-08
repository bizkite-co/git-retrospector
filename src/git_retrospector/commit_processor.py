#!/usr/bin/env python3
import subprocess
import logging
import toml
import time
from git_retrospector.git_utils import enable_junit_reporter_playwright


def process_commit(remote_repo_path, commit_hash, output_dir, origin_branch, retro):
    """
    Checks out a specific commit in the target repository, runs tests, and
    returns to the original branch.

    Args:
        remote_repo_path (str): The path to the target repository.
        commit_hash (str): The hash of the commit to process.
        output_dir (str): The base output directory.
        origin_branch (str): The original branch to return to.
        retro (Retro): The configuration object.
    """
    logging.info(f"process_commit called with hash: {commit_hash}")

    if origin_branch is None:
        return

    # Load the retro.toml file to access test_runners *BEFORE* changing directory
    config_file_path = retro.get_config_file_path()
    with open(config_file_path) as config_file:
        config_data = toml.load(config_file)

    # Ensure test_runners exists and is a list
    test_runners = config_data.get("test_runners", [])
    if not isinstance(test_runners, list):
        logging.error("test_runners in retro.toml must be a list")
        return

    commit_hash_dir, tool_summary_dir = retro.create_commit_hash_dir(commit_hash)
    logging.info(f"Created directory: {commit_hash_dir}")

    try:
        # Change to the target repo directory
        retro.change_to_repo_dir()
        subprocess.run(
            ["git", "reset", "--hard", "HEAD"],
            check=False,
            capture_output=False,
            cwd=str(remote_repo_path),
        )
        # Checkout the commit
        subprocess.run(
            ["git", "checkout", commit_hash],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(remote_repo_path),  # Use the remote repo path as cwd
        )

        # Enable JUnit reporter for Playwright
        enable_junit_reporter_playwright(retro.remote_repo_path)

    except subprocess.CalledProcessError as e:
        logging.error(f"Error during git checkout {commit_hash}: {e}")
        retro.restore_cwd()  # Need to restore CWD even if checkout fails
        return  # need to return here, so we don't try to run tests if checkout failed

    try:
        for test_runner in test_runners:
            try:
                retro.run_tests(test_runner, commit_hash)
            except Exception:
                logging.info("commit_processor test_runner: {e}")
            finally:
                retro.move_test_results_to_local(commit_hash, test_runner["output_dir"])
                time.sleep(1)  # Added delay
    finally:
        retro.restore_cwd()  # Restore CWD even if checkout fails
