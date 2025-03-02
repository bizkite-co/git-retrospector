#!/usr/bin/env python3
import subprocess
import os
import logging


def run_vitest(target_repo, output_dir, retro):
    """Runs vitest tests and captures output."""
    # if Retro.is_test_environment():
    #     logging.info("Skipping vitest execution in test environment.")
    #     return

    command = [
        "npm",
        "run",
        "test",
        "--",
        "--run",
        f"--outputFile={retro.get_vitest_log_path(retro.get_commit_hash_dir(output_dir)[0])}",
    ]
    try:
        # Explicitly change directory
        logging.info(f"Running vitest with command: {command}")
        original_cwd = os.getcwd()
        logging.info(f"Original cwd: {original_cwd}")
        os.chdir(target_repo)
        logging.info(f"Changed cwd to: {os.getcwd()}")
        subprocess.run(command, check=True, capture_output=True, text=True)

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
    """Runs playwright tests and captures output."""
    # if Retro.is_test_environment():
    #     logging.info("Skipping playwright execution in test environment.")
    #     return
    commit_hash_dir, tool_summary_dir = retro.get_commit_hash_dir(output_dir)
    command = [
        "npx",
        "playwright",
        "test",
        "--reporter=junit",
        f"--output={retro.get_playwright_xml_path(retro.get_commit_hash_dir(output_dir)[0])}",
    ]

    try:
        logging.info(f"Running playwright with command: {command}")
        result = subprocess.run(
            command, cwd=target_repo, check=True, capture_output=True, text=True
        )
        logging.info(f"Playwright output: {result.stdout}")

    except subprocess.CalledProcessError as e:
        logging.error(f"Error running playwright: {e}")
        logging.error(f"stdout: {e.stdout}")
        logging.error(f"stderr: {e.stderr}")
        raise e
