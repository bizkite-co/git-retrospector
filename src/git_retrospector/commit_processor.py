#!/usr/bin/env python3
import subprocess
import logging
import toml
import time


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
        # Load the retro.toml file to access test_runners
        config_file_path = retro.get_config_file_path()
        with open(config_file_path) as config_file:
            config_data = toml.load(config_file)

        # Ensure test_runners exists and is a list
        test_runners = config_data.get("test_runners", [])
        if not isinstance(test_runners, list):
            logging.error("test_runners in retro.toml must be a list")
            return

        for test_runner in test_runners:
            try:
                retro.run_tests(test_runner, commit_hash)
            except Exception:  # Removed unused variable 'e'
                logging.info("commit_processor test_runner: {e}")
            finally:
                retro.move_test_results_to_local(commit_hash, test_runner["output_dir"])
                time.sleep(1)  # Added delay
    finally:
        pass

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
