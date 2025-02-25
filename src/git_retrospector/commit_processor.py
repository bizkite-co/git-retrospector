#!/usr/bin/env python3
import os
import shutil
import subprocess
from pathlib import Path

from git_retrospector.runners import run_playwright, run_vitest


def process_commit(target_repo, commit_hash, output_dir, origin_branch, config):
    """
    Checks out a specific commit in the target repository, runs tests, and
    returns to the original branch.

    Args:
        target_repo (str): The path to the target repository.
        commit_hash (str): The hash of the commit to process.
        output_dir (str): The base output directory.
        origin_branch (str): The original branch to return to.
        config (Config): The configuration object.
    """
    output_dir_for_commit = config.test_result_dir / "test-output" / commit_hash
    output_dir_for_commit.mkdir(parents=True, exist_ok=True)

    if origin_branch is None:
        return

    try:
        subprocess.run(
            ["git", "checkout", "--force", commit_hash],
            cwd=target_repo,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return

    run_vitest(target_repo, str(output_dir_for_commit), config)
    run_playwright(target_repo, str(output_dir_for_commit), config)

    # Move Playwright output to the correct location
    try:
        source_dir = Path(target_repo) / "test-results"
        if source_dir.exists():
            for item in os.listdir(source_dir):
                s = os.path.join(source_dir, item)
                d = os.path.join(output_dir_for_commit, item)
                if os.path.isdir(s):
                    shutil.move(s, d)
                else:
                    shutil.move(s, d)
            shutil.rmtree(source_dir)  # Remove the source directory after moving

        # Rename playwright.log to playwright.xml
        playwright_log_path = os.path.join(output_dir_for_commit, "playwright.log")
        playwright_xml_path = os.path.join(output_dir_for_commit, "playwright.xml")
        if os.path.exists(playwright_log_path):
            os.rename(playwright_log_path, playwright_xml_path)

    except Exception:
        pass

    try:
        subprocess.run(
            ["git", "checkout", "--force", origin_branch],
            cwd=target_repo,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return
