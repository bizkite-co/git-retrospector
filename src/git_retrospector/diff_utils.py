#!/usr/bin/env python3
import subprocess
from pathlib import Path
from git_retrospector.retro import Retro
import logging  # Import logging
import re  # Import re for more robust parsing


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
    output_path_obj = Path(output_path)
    commit_hash = (
        output_path_obj.parent.name
    )  # Get the parent directory name (commit hash)
    retro.create_output_dirs(commit_hash=commit_hash)

    # Generate the diff
    try:
        result = subprocess.run(
            ["git", "diff", commit1, commit2],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,  # Check=True is appropriate here, failure means diff failed
        )
        # Save the diff to the output file
        with open(output_path_obj, "w") as f:
            f.write(result.stdout)
    except subprocess.CalledProcessError as e:
        # Log the error for better debugging
        logging.error(f"Error generating diff between {commit1} and {commit2}: {e}")
        logging.error(f"Stderr: {e.stderr}")
        raise RuntimeError(f"Error generating diff: {e}") from e
    except Exception as e:
        logging.error(f"Unexpected error writing diff file {output_path_obj}: {e}")
        raise


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
    filtered_lines = []
    current_file_is_target = False  # Flag for the current file block
    # Regex to capture the 'b/' filename, handling potential quotes
    diff_git_pattern = re.compile(r'^diff --git a/.+ b/(?:"?([^"]+)"?|([^ ]+))$')

    for line in diff_content.splitlines():
        match = diff_git_pattern.match(line)
        if match:
            # Reset flag for the new file block
            current_file_is_target = False
            # Extract filename (group 1 for quoted, group 2 for unquoted)
            current_file = match.group(1) or match.group(2)
            if current_file and current_file in filenames:
                current_file_is_target = True
                filtered_lines.append(line)  # Add the 'diff --git' line itself
            # else: # Debugging
            #     logging.debug(f"Diff filter: Skipping file {current_file}")

        elif current_file_is_target:
            # If we are inside a block for a target file, add the line
            filtered_lines.append(line)

    # Join lines adding back the newline character, ensuring consistent trailing newline
    if not filtered_lines:
        return ""
    else:
        # Ensure the result ends with exactly one newline
        result = "\n".join(filtered_lines)
        if not result.endswith("\n"):
            result += "\n"
        return result
