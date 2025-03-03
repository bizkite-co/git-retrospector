#!/usr/bin/env python3
import subprocess
import logging
import os


def process_commit(target_repo, commit_hash, output_dir, origin_branch, retro):
    """
    Checks out a specific commit in the target repository, runs tests, and
    returns to the original branch.

    Args:
        target_repo (str): The path to the target repository.
        commit_hash (str): The hash of the commit to process.
        output_dir (str): The base output directory.
        origin_branch (str): The original branch to return to.
        retro (Retro): The configuration object.
    """
    logging.info(f"process_commit called with hash: {commit_hash}")

    if origin_branch is None:
        return

    original_cwd = os.getcwd()  # Store the original CWD

    try:
        # Use git --work-tree to checkout commit into the target_repo directory
        subprocess.run(
            ["git", "--work-tree=" + target_repo, "checkout", commit_hash, "--", "."],
            cwd=target_repo,  # Specify the original repo as cwd
            check=True,
            capture_output=True,
            text=True,
        )

    except subprocess.CalledProcessError as e:
        logging.error(f"Error during git checkout {commit_hash}: {e}")
        return  # need to return here, so we don't try to run tests if checkout failed

    try:
        os.chdir(target_repo)  # Change to the target repo directory
        retro.run_tests("vitest", commit_hash)
        retro.run_tests("playwright", commit_hash)
    finally:
        os.chdir(original_cwd)  # Restore original CWD

    try:
        subprocess.run(
            ["git", "checkout", "--force", origin_branch],
            cwd=target_repo,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during git checkout {origin_branch}: {e}")
        return
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
