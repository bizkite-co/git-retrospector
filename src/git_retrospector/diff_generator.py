#!/usr/bin/env python3
import logging
from git_retrospector.retro import Retro
from git_retrospector.diff_utils import generate_diff


def generate_commit_diffs(retro: Retro) -> None:
    """
    Generates diff files for each commit in commits.log within the retro directory.

    Args:
        retro: The Retro object.
    """
    commits_log_path = retro.get_commits_log_path()
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
            output_path = (
                retro.get_test_output_dir(current_commit)
                + f"/{previous_commit}_{current_commit}.diff"
            )
            try:
                logging.debug(
                    f"""repo_path: {
                        retro.repo_under_test_path
                    }, commit1: {previous_commit},"""
                    f"commit2: {current_commit}, output_path: {output_path}"
                )
                generate_diff(
                    retro,
                    str(retro.repo_under_test_path),
                    previous_commit,
                    current_commit,
                    output_path,
                )
            except Exception as e:
                logging.error(
                    f"Error: diff for {previous_commit} -> {current_commit}: {e}"
                )
        previous_commit = current_commit
