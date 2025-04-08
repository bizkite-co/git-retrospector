import os
import subprocess
import logging
from typing import List, Dict  # Added List, Dict, Optional, Any


def get_origin_branch_or_commit(repo_path):
    """Gets the origin branch or commit hash for a given repo path."""
    try:
        # Try to get the current branch name
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        branch_name = result.stdout.strip()
        if branch_name != "HEAD":  # Check if it's a detached HEAD state
            return branch_name

        # If it's a detached HEAD, get the commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_current_commit_hash(repo_path):
    """Gets the current commit hash for a given repo path."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def enable_junit_reporter_playwright(remote_repo_path):
    """
    Enables the JUnit reporter in the playwright.config.ts file.

    Args:
        remote_repo_path: The path to the remote repository.
    """
    config_file_path = os.path.join(remote_repo_path, "playwright.config.ts")
    logging.info(f"Checking for playwright config file at: {config_file_path}")

    if not os.path.exists(config_file_path):
        logging.error(f"Playwright config file not found: {config_file_path}")
        return

    try:
        with open(config_file_path) as f:
            config_content = f.read()
    except Exception as e:
        logging.error(f"Error reading playwright config file: {e}")
        return

    new_line = "  reporter: [['list'], ['junit' ]],"
    try:
        if "reporter:" in config_content:
            updated_content = ""
            for line in config_content.splitlines():
                if "reporter:" in line:
                    updated_content += new_line + "\n"
                else:
                    updated_content += line + "\n"
        else:
            updated_content = config_content.replace(
                "use: {", f"use: {{\n    {new_line}\n"
            )

    except Exception as e:
        logging.error(f"Error updating playwright config: {e}")
        return

    try:
        with open(config_file_path, "w") as f:
            f.write(updated_content)
    except Exception as e:
        logging.error(f"Error writing updated playwright config: {e}")
        return


def ensure_screenshots_branch(repo_path, branch_name="test-screenshots"):
    """
    Ensures that the specified branch exists in the remote repository.
    Creates the branch if it doesn't exist locally or remotely.
    """
    try:
        # Get the current branch
        current_branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path, text=True
        ).strip()

        # Check if the branch exists locally
        result = subprocess.run(
            ["git", "branch", "--list", branch_name],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,  # Don't raise an exception if branch doesn't exist
        )
        if branch_name in result.stdout:
            if current_branch == branch_name:
                logging.info(f"Already on branch '{branch_name}'.")
                return True  # Already on the correct branch

            # Branch exists locally, switch to it and pull
            logging.info(
                f"Branch '{branch_name}' exists locally. Switching and pulling..."
            )
            subprocess.run(
                ["git", "checkout", branch_name],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "pull", "origin", branch_name],
                cwd=repo_path,
                check=False,  # might not exist on remote yet
                capture_output=True,
                text=True,
            )
        else:
            # Branch doesn't exist locally, check remotely
            try:
                subprocess.run(
                    [
                        "git",
                        "ls-remote",
                        "--exit-code",
                        "--heads",
                        "origin",
                        branch_name,
                    ],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logging.info(f"Branch '{branch_name}' exists remotely. Fetching...")
                # Branch exists remotely, fetch and checkout
                subprocess.run(
                    ["git", "fetch", "origin", f"{branch_name}:{branch_name}"],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    ["git", "checkout", branch_name],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            except subprocess.CalledProcessError:
                # Branch doesn't exist remotely, create it
                logging.info(
                    f"Branch '{branch_name}' does not exist remotely. Creating..."
                )
                # Fetch origin to make sure we have the latest refs
                subprocess.run(
                    ["git", "fetch", "origin"],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                # Create the branch from the main branch
                # (or master, if main doesn't exist)
                main_branch = subprocess.run(
                    ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if main_branch.returncode == 0:
                    default_branch = main_branch.stdout.strip().replace(
                        "refs/remotes/origin/", ""
                    )
                else:  # default to main
                    default_branch = "main"

                subprocess.run(
                    ["git", "checkout", "-b", branch_name, f"origin/{default_branch}"],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                # Push the new branch to the remote
                subprocess.run(
                    ["git", "push", "-u", "origin", branch_name],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logging.info(f"Branch '{branch_name}' created and pushed to remote.")

        # Switch back to the original branch
        if current_branch != branch_name:
            subprocess.run(
                ["git", "checkout", current_branch],
                cwd=repo_path,
                check=False,  # don't fail if we can't switch back
                capture_output=True,
                text=True,
            )

    except subprocess.CalledProcessError as e:
        logging.error(f"Error ensuring branch '{branch_name}': {e}")
        return False

    return True


def get_commit_list(repo_path: str, num_commits: int) -> List[Dict[str, str]]:
    """
    Retrieves a list of the last N commits from the repository.

    Args:
        repo_path: The path to the Git repository.
        num_commits: The number of commits to retrieve.

    Returns:
        A list of dictionaries, where each dictionary represents a commit
        with 'hash', 'date', and 'summary' keys. Returns an empty list on error.
    """
    commit_list: List[Dict[str, str]] = []
    try:
        # Construct the git log command
        command = [
            "git",
            "log",
            "--pretty=format:%H|%ad|%s",
            "--date=iso",
            f"-n{num_commits}",
        ]
        logging.debug(f"Executing command: {' '.join(command)} in {repo_path}")

        result = subprocess.run(
            command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )

        output = result.stdout.strip()
        for line in output.splitlines():
            parts = line.split("|", 2)  # Split into max 3 parts
            if len(parts) == 3:
                commit_list.append(
                    {"hash": parts[0], "date": parts[1], "summary": parts[2]}
                )
            else:
                logging.warning(f"Skipping malformed commit line: {line}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting commit list from {repo_path}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while getting commit list: {e}")

    return commit_list
