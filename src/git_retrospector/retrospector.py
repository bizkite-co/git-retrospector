#!/usr/bin/env python3
import argparse
import csv
import os
import subprocess
from pathlib import Path
import logging

import toml
from pydantic import ValidationError

from git_retrospector.config import Config
from git_retrospector.git_utils import (
    get_current_commit_hash,
    get_origin_branch_or_commit,
)
from git_retrospector.commit_processor import process_commit
from git_retrospector.diff_generator import generate_commit_diffs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def run_tests(target_name, iteration_count):
    """
    Runs tests on a range of commits in the target repository.

        target_name (str): The name of the target repository (used to locate the
            config file).
        iteration_count (int): The number of commits to go back in history.
    """
    # Load config
    config_file_path = os.path.join("retros", target_name, "config.toml")
    try:
        with open(config_file_path) as config_file:
            config_data = toml.load(config_file)
        config = Config(**config_data)
        target_repo = str(config.repo_under_test_path)
        test_output_dir = str(config.test_result_dir)
    except FileNotFoundError:
        print(  # noqa: T201
            f"Error: Config file not found: {config_file_path}\n"
            f"Please run: './retrospector.py init {target_name} <target_repo_path>'"
        )
        logging.error(f"Config file not found: {config_file_path}")
        return
    except (KeyError, toml.TomlDecodeError) as e:
        logging.error(f"Error reading config file: {e}")
        return
    except ValidationError as e:
        logging.error(f"Error validating config file: {e}")
        return

    commits_log_path = Path(config.test_result_dir) / "commits.log"
    with open(commits_log_path, "w") as commits_log:
        origin_branch = get_origin_branch_or_commit(target_repo)

        # Check if target_repo is a git repository
        assert origin_branch is not None, (
            "Error: Target repo directory {target_repo} is not a git "
            "repository or does not exist"
        )

        logging.info(f"Running tests for {target_name} ({iteration_count} iterations)")

        # Use get_current_commit_hash to get the initial HEAD *before* the loop
        current_commit = get_current_commit_hash(target_repo)
        if current_commit is None:
            return
        for i in range(iteration_count):
            logging.info(f"Iteration: {i}")
            try:
                commit_hash_result = subprocess.run(
                    ["git", "rev-parse", "--short", f"{current_commit}~{i}"],
                    cwd=target_repo,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                logging.debug(f"rev-parse result: {commit_hash_result.stdout.strip()}")
                commit_hash = commit_hash_result.stdout.strip()
                if not commit_hash:
                    continue  # Skip this iteration

                process_commit(
                    target_repo, commit_hash, test_output_dir, origin_branch, config
                )
                commits_log.write(f"{commit_hash}\\n")
            except subprocess.CalledProcessError as e:
                logging.error(f"Error processing commit {current_commit}~{i}: {e}")
                continue


def analyze_test_results(retro_name):
    """
    Analyzes test results for a given retro.
    """
    # Import here to avoid circular dependency
    from git_retrospector.parser import process_retro

    process_retro(retro_name)
    generate_commit_diffs(os.path.join("retros", retro_name))


def find_test_summary_files(commit_dir):
    """
    Locates the playwright.csv and vitest.csv files within the tool-summary
    subdirectory.
    Raises FileNotFoundError if the directory or files don't exist.
    """
    tool_summary_dir = os.path.join(commit_dir, "tool-summary")
    if not os.path.exists(tool_summary_dir):
        raise FileNotFoundError(f"Tool summary directory not found: {tool_summary_dir}")

    playwright_csv = os.path.join(tool_summary_dir, "playwright.csv")
    vitest_csv = os.path.join(tool_summary_dir, "vitest.csv")

    if not os.path.exists(playwright_csv):
        playwright_csv = None
    if not os.path.exists(vitest_csv):
        vitest_csv = None

    return playwright_csv, vitest_csv


def count_failed_tests(csv_file):
    """Counts the number of failed tests in a given CSV file."""
    failed_count = 0
    try:
        with open(csv_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Result") == "failed":
                    failed_count += 1
    except Exception as e:
        logging.error(f"Error reading CSV file {csv_file}: {e}")
        return -1  # Indicate an error
    return failed_count


def load_config_for_retro(retro_name):
    """Loads the configuration for a given retro."""
    config_file_path = os.path.join("retros", retro_name, "config.toml")
    with open(config_file_path) as config_file:
        config_data = toml.load(config_file)
    config = Config(**config_data)
    return config.repo_under_test_owner, config.repo_under_test_name


def get_user_confirmation(failed_count):
    """Gets user confirmation to proceed with creating issues."""
    while True:
        user_input = input(
            f"Found {failed_count} failed tests. Create GitHub issues? (y/n): "
        ).lower()
        if user_input in ["y", "n"]:
            return user_input == "y"


def process_csv_files(repo, playwright_csv, vitest_csv):
    """Processes CSV files and creates issues for failed tests."""
    for csv_file in [playwright_csv, vitest_csv]:
        if csv_file:
            with open(csv_file) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Result") == "failed":
                        title = row.get("Test Name", "Unnamed Test")
                        body = (
                            f"Error: {row.get('Error', 'No error message')}\n"
                            f"Stack Trace: {row.get('Stack Trace', 'No stack trace')}\n"
                            # TODO: Add screenshot link if available
                        )
                        repo.create_issue(title=title, body=body)


def should_create_issues(retro_name, commit_hash):
    """Checks if conditions are met to create GitHub issues."""
    commit_dir = os.path.join("retros", retro_name, "test-output", commit_hash)
    if not os.path.exists(commit_dir):
        return False

    playwright_csv, vitest_csv = find_test_summary_files(commit_dir)

    if not playwright_csv and not vitest_csv:
        return False

    failed_count = 0
    for csv_file in [playwright_csv, vitest_csv]:
        if csv_file:
            count = count_failed_tests(csv_file)
            if count == -1:
                return False  # Stop if there was an error reading a file
            failed_count += count

    if failed_count == 0:
        return False

    return get_user_confirmation(failed_count)


def handle_failed_tests(retro_name, commit_hash):
    """Handles the process of finding and reporting failed tests."""
    commit_dir = os.path.join("retros", retro_name, "test-output", commit_hash)
    if not os.path.exists(commit_dir):
        return

    playwright_csv, vitest_csv = find_test_summary_files(commit_dir)
    if not playwright_csv and not vitest_csv:
        return

    failed_count = 0
    for csv_file in [playwright_csv, vitest_csv]:
        if csv_file:
            count = count_failed_tests(csv_file)
            if count == -1:
                return  # Stop if there was an error reading a file
            failed_count += count

    if failed_count == 0:
        return

    return failed_count


def create_github_issues(repo_owner, repo_name, playwright_csv, vitest_csv):
    """Creates GitHub issues based on failed test data."""
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        return

    from github import Github

    g = Github(token)

    try:
        repo = g.get_user(repo_owner).get_repo(repo_name)
    except Exception as e:
        logging.error(f"Error getting repository {repo_owner}/{repo_name}: {e}")
        return
    process_csv_files(repo, playwright_csv, vitest_csv)


def create_issues_for_commit(retro_name, commit_hash):
    """
    Creates GitHub issues for failed tests in a specific commit.
    """
    if not should_create_issues(retro_name, commit_hash):
        print("should_create_issues returned False")  # noqa: T201
        return

    repo_owner, repo_name = load_config_for_retro(retro_name)
    if not repo_owner or not repo_name:
        print("Could not load repo owner or name")  # noqa: T201
        return

    commit_dir = os.path.join("retros", retro_name, "test-output", commit_hash)
    create_github_issues(repo_owner, repo_name, *find_test_summary_files(commit_dir))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run tests on a range of commits and parse results."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'init' command
    init_parser = subparsers.add_parser("init", help="Initialize a target repository")
    init_parser.add_argument("target_name", help="Name of the target repository")
    init_parser.add_argument("target_repo_path", help="Path to the target repository")

    # 'run' command
    run_parser = subparsers.add_parser("run", help="Run tests on a target repository")
    run_parser.add_argument(
        "target_name",
        help="Name of the target repository (must be initialized first)",
    )
    run_parser.add_argument(
        "-i",
        "--iterations",
        type=int,
        default=10,
        help="Number of iterations (default: 10)",
    )
    run_parser.add_argument(
        "-c", "--commit_dir", help="Specific commit directory to process"
    )

    # 'issues' command
    issues_parser = subparsers.add_parser(
        "issues", help="Create GitHub issues for failed tests in a specific commit"
    )
    issues_parser.add_argument("retro_name", help="Name of the retro")
    issues_parser.add_argument("commit_hash", help="Commit hash to analyze")

    args = parser.parse_args()

    if args.command == "init":
        Config.initialize(args.target_name, args.target_repo_path)
    elif args.command == "run":
        run_tests(args.target_name, args.iterations)
        analyze_test_results(args.target_name)
    elif args.command == "issues":
        create_issues_for_commit(args.retro_name, args.commit_hash)
    else:
        parser.print_help()
