#!/usr/bin/env python3
import subprocess
from pathlib import Path
import logging
import os

from git_retrospector.runners import run_playwright, run_vitest


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

    original_cwd = os.getcwd()  # Get the original working directory
    logging.info(f"Original cwd in process_commit: {original_cwd}")
    try:
        # Use git --work-tree to checkout commit into the target_repo directory
        logging.info(f"target_repo before checkout: {target_repo}")
        subprocess.run(
            ["git", "--work-tree=" + target_repo, "checkout", commit_hash, "--", "."],
            cwd=target_repo,  # Specify the original repo as cwd
            check=True,
            capture_output=True,
            text=True,
        )
        logging.info(f"target_repo after checkout: {target_repo}")
        logging.info(f"Current working directory after checkout: {os.getcwd()}")

    except subprocess.CalledProcessError as e:
        logging.error(f"Error during git checkout {commit_hash}: {e}")
        return  # need to return here, so we don't try to run tests if checkout failed

    logging.info(f"Current working directory before running tests: {os.getcwd()}")
    logging.info(
        f"""run_vitest command: {
            run_vitest(target_repo, retro.get_tool_summary_dir(commit_hash), retro)
        }"""
    )
    run_vitest(target_repo, retro.get_tool_summary_dir(commit_hash), retro)
    logging.info(
        f"""run_playwright command: {
            run_playwright(target_repo, retro.get_tool_summary_dir(commit_hash), retro)
        }"""
    )
    run_playwright(target_repo, retro.get_tool_summary_dir(commit_hash), retro)

    # Move Playwright output to the correct location (next to tool-summary)
    try:
        source_dir = Path(target_repo) / "test-results"
        logging.info(f"Checking for existence of test-results directory: {source_dir}")
        if source_dir.exists():
            logging.info(
                f"Moving test results from {source_dir} to "
                f"{retro.get_test_output_dir(commit_hash)}"
            )
            retro.move_test_results(commit_hash)

        # Rename playwright.log to playwright.xml (now in the correct location)
        playwright_log_path = retro.get_playwright_log_path(commit_hash)
        logging.info(f"playwright_log_path: {playwright_log_path}")
        if playwright_log_path.exists():
            logging.info(f"Renaming {playwright_log_path} to playwright.xml")
            retro.rename_file(str(playwright_log_path), "playwright.xml")

    except Exception as e:
        logging.error(f"Error moving files: {e}")

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
    finally:
        os.chdir(original_cwd)  # change back to the original cwd
