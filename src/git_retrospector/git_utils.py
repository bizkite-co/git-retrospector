#!/usr/bin/env python3
import subprocess
import logging


def get_original_branch(target_repo):
    """Gets the original Git branch of the repository.

    Args:
        target_repo (str): Path to the Git repository.

    Returns:
        str: The original branch name, or None if an error occurs.
    """
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            cwd=target_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting original branch: {e}")
        return None


def get_current_commit_hash(target_repo):
    """Gets the current commit hash of the repository.

    Args:
        target_repo (str): Path to the Git repository.

    Returns:
        str: The current commit hash, or None if an error occurs.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=target_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting current commit hash: {e}")
        return None


def get_origin_branch_or_commit(target_repo):
    """
    Gets the original Git branch of the repository. If the branch cannot be determined
    (e.g., the repo is in a detached HEAD state), returns the current commit hash.

    Args:
        target_repo (str): Path to the Git repository.

    Returns:
        str: The original branch name or the current commit hash.
    """
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            cwd=target_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()  # Return the branch name
    except subprocess.CalledProcessError:
        # print("Could not determine original branch. Using current commit.")
        return get_current_commit_hash(target_repo)  # Fallback to commit hash
