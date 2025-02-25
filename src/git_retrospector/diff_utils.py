#!/usr/bin/env python3
import subprocess
import os


def generate_diff(repo_path: str, commit1: str, commit2: str, output_path: str) -> None:
    """
    Generates a diff file between two commits and saves it to the specified output path.

    Args:
        repo_path: The path to the Git repository.
        commit1: The hash of the first commit.
        commit2: The hash of the second commit.
        output_path: The full path to where the diff file should be saved.

    Raises:
        ValueError: If either commit1 or commit2 is not a valid commit hash.
        subprocess.CalledProcessError: If the git diff command fails.
    """
    # Validate commit hashes
    try:
        subprocess.run(
            ["git", "rev-parse", "--verify", commit1],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        subprocess.run(
            ["git", "rev-parse", "--verify", commit2],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Invalid commit hash: {e}") from e

    # Create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Generate the diff
    try:
        result = subprocess.run(
            ["git", "diff", commit1, commit2],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        # Save the diff to the output file
        with open(output_path, "w") as f:
            f.write(result.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error generating diff: {e}") from e
