#!/usr/bin/env python3
import subprocess
from pathlib import Path
from git_retrospector.retro import Retro


def generate_diff(
    retro: Retro, repo_path: str, commit1: str, commit2: str, output_path: str
) -> None:
    """
    Generates a diff file between two commits and saves it to the specified output path.

    Args:
        retro: The Retro object
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
    # output_path is something like:
    # retros/test_retro/test-output/hash2/hash1_hash2.diff
    commit_hash = Path(output_path).parts[-2]
    commit_hash_dir, _ = retro.get_commit_hash_dir(commit_hash)
    retro.create_output_dirs(commit_hash=commit_hash)

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


def filter_diff_by_filenames(diff_content: str, filenames: list[str]) -> str:
    """
    Filters a diff content string to include only changes related to specified files.

    Args:
        diff_content: The original diff content as a string.
        filenames: A list of filenames to include in the filtered diff.

    Returns:
        A string containing only the diff hunks related to the specified files.
        If no matches are found, returns an empty string.
    """
    filtered_diff = []
    include_current_file = False

    for line in diff_content.splitlines():
        if line.startswith("diff --git"):
            parts = line.split(" ")
            current_file = None
            for part in parts:
                if part.startswith("b/"):
                    current_file = part[2:]
                    break
            if current_file:  # Check if current_file was found
                include_current_file = current_file in filenames
        if include_current_file:
            filtered_diff.append(line)

    return "\n".join(filtered_diff) if filtered_diff else ""
