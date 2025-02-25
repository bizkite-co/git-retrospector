#!/usr/bin/env python3
import os
import toml
from pydantic import ValidationError
from git_retrospector.config import Config
from git_retrospector.diff_utils import generate_diff


def generate_commit_diffs(retro_dir: str) -> None:
    """
    Generates diff files for each commit in commits.log within the retro directory.

    Args:
        retro_dir: Path to the retro directory (e.g., 'retros/handterm').
    """
    commits_log_path = os.path.join(retro_dir, "commits.log")
    config_file_path = os.path.join(retro_dir, "config.toml")
    try:
        with open(config_file_path) as config_file:
            config_data = toml.load(config_file)
        config = Config(**config_data)
        repo_path = str(config.repo_under_test_path)  # Correct repo path
        test_output_dir = config.test_result_dir
    except (FileNotFoundError, KeyError, toml.TomlDecodeError, ValidationError):
        print(f"Error: Could not load config from {config_file_path}")  # noqa T201
        return

    try:
        with open(commits_log_path) as f:
            commit_hashes = f.read().splitlines()
    except FileNotFoundError:
        return  # Exit if commits.log is missing

    if not commit_hashes:
        return  # Exit if commits.log is empty

    previous_commit = None
    for current_commit in commit_hashes:
        if previous_commit is not None:
            output_path = os.path.join(
                str(test_output_dir),
                "test-output",
                current_commit,
                f"{previous_commit}_{current_commit}.diff",
            )
            try:
                print(  # noqa: T201
                    f"repo_path: {repo_path}, commit1: {previous_commit}, "
                    f"commit2: {current_commit}, output_path: {output_path}"
                )
                generate_diff(repo_path, previous_commit, current_commit, output_path)
            except Exception as e:
                print(  # noqa: T201
                    f"Error: diff for {previous_commit} -> {current_commit}: {e}"
                )
        previous_commit = current_commit
