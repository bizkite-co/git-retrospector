import os
import subprocess
import logging


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
