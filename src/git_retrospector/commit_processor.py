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
    tool_summary_dir = output_dir_for_commit / "tool-summary"
    tool_summary_dir.mkdir(parents=True, exist_ok=True)

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

    run_vitest(target_repo, str(tool_summary_dir), config)
    run_playwright(target_repo, str(tool_summary_dir), config)

    # Move vitest.csv and playwright.csv
    try:
        source_dir = Path(target_repo)
        if source_dir.exists():
            for item in ["vitest.csv", "playwright.csv"]:
                s = os.path.join(source_dir, item)
                d = os.path.join(tool_summary_dir, item)
                if os.path.exists(s):
                    shutil.move(s, d)

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
