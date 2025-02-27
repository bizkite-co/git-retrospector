#!/usr/bin/env python3
import csv
import logging
import os
import subprocess
import sys
from pathlib import Path

import click
import toml
from github import Github, GithubException
from pydantic import ValidationError
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from git_retrospector.commit_processor import process_commit
from git_retrospector.config import Config
from git_retrospector.diff_generator import generate_commit_diffs
from git_retrospector.git_utils import (
    get_current_commit_hash,
    get_origin_branch_or_commit,
)

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
        click.echo(
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

    g = Github(token)

    try:
        repo = g.get_user(repo_owner).get_repo(repo_name)
    except Exception as e:
        logging.error(f"Error getting repository {repo_owner}/{repo_name}: {e}")
        return
    process_csv_files(repo, playwright_csv, vitest_csv)


def upload_screenshot_to_github(screenshot_path, repo_owner, repo_name):
    """
    Uploads a screenshot to the GitHub repository.

    Args:
        screenshot_path (str): The absolute path to the screenshot file.
        repo_owner (str): The owner of the GitHub repository.
        repo_name (str): The name of the GitHub repository.

    Returns:
        str: The URL of the uploaded screenshot, or None if the upload fails.
    """
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        logging.error("GitHub personal access token not found.")
        return None

    g = Github(token)

    try:
        repo = g.get_user(repo_owner).get_repo(repo_name)
        with open(screenshot_path, "rb") as f:
            content = f.read()

        # Create a unique file name for the screenshot
        screenshot_name = os.path.basename(screenshot_path)
        upload_path = f"screenshots/{screenshot_name}"

        try:
            # Check if the file already exists
            repo.get_contents(upload_path)
            logging.warning(f"Screenshot already exists at {upload_path}")
            return (
                f"https://github.com/{repo_owner}/{repo_name}/blob/main/{upload_path}"
            )
        except GithubException as e:
            if e.status == 404:  # File does not exist, proceed with upload
                repo.create_file(
                    upload_path,
                    f"Upload screenshot {screenshot_name}",
                    content,
                    branch="main",
                )
                return f"""
                    https://github.com/{
                    repo_owner}/{repo_name
                    }/blob/main/{upload_path}"""  # Raw URL
            else:
                logging.error(f"Error checking for existing screenshot: {e}")
                return None

    except Exception as e:
        logging.error(f"Error uploading screenshot: {e}")
        return None


def create_issues_for_commit(retro_name, commit_hash):
    """
    Creates GitHub issues for failed tests in a specific commit.
    """
    if not should_create_issues(retro_name, commit_hash):
        logging.info("should_create_issues returned False")  # TODO: Convert to CLI
        return

    repo_owner, repo_name = load_config_for_retro(retro_name)
    if not repo_owner or not repo_name:
        logging.info("Could not load repo owner or name")  # TODO: Convert to CLI
        return

    commit_dir = os.path.join("retros", retro_name, "test-output", commit_hash)
    create_github_issues(repo_owner, repo_name, *find_test_summary_files(commit_dir))


def handle_no_command():
    command_completer = WordCompleter(["init", "run", "issues"], ignore_case=True)
    command_str = prompt(
        "Enter a command (or press Ctrl-D to exit): ", completer=command_completer
    )
    if command_str:
        command_parts = command_str.split()
        command_name = command_parts[0]
        if command_name == "init":
            handle_init_command(command_parts)
        elif command_name == "run":
            handle_run_command(command_parts)
        elif command_name == "issues":
            handle_issues_command(command_parts)
        else:
            click.echo(f"Unknown command: {command_name}")


def handle_init_command(command_parts):
    if len(command_parts) == 3:
        target_name = command_parts[1]
        target_repo_path = command_parts[2]
        init(target_name, target_repo_path)
    else:
        click.echo("Usage: init <target_name> <target_repo_path>")


def handle_run_command(command_parts):
    if len(command_parts) >= 2:
        target_name = command_parts[1]
        #  Handle optional arguments for run
        iterations = 10
        commit_dir = None
        if "-i" in command_parts:
            try:
                iterations_index = command_parts.index("-i") + 1
                iterations = int(command_parts[iterations_index])
            except (ValueError, IndexError):
                click.echo("Invalid value for iterations.")
                return
        if "-c" in command_parts:
            try:
                commit_dir_index = command_parts.index("-c") + 1
                commit_dir = command_parts[commit_dir_index]
            except IndexError:
                click.echo("Invalid value for commit_dir")
                return
        run(target_name, iterations, commit_dir)

    else:
        click.echo("Usage: run <target_name> [-i iterations] [-c commit_dir]")


def handle_issues_command(command_parts):
    if len(command_parts) == 3:
        retro_name = command_parts[1]
        commit_hash = command_parts[2]
        issues(retro_name, commit_hash)
    else:
        click.echo("Usage: issues <retro_name> <commit_hash>")


@click.group()
def cli():
    """Run tests on a range of commits and parse results."""
    if not any(arg in sys.argv for arg in ["init", "run", "issues"]):
        handle_no_command()


@cli.command()
@click.argument("target_name")
@click.argument("target_repo_path")
def init(target_name, target_repo_path):
    """Initialize a target repository."""
    Config.initialize(target_name, target_repo_path)


@cli.command()
@click.argument("target_name")
@click.option(
    "-i",
    "--iterations",
    type=int,
    default=10,
    help="Number of iterations (default: 10)",
)
@click.option("-c", "--commit_dir", help="Specific commit directory to process")
def run(target_name, iterations, commit_dir):
    """Run tests on a target repository."""
    if not any(arg in sys.argv for arg in ["-i", "--iterations", "-c", "--commit_dir"]):
        config_file_path = os.path.join("retros", target_name, "config.toml")
        try:
            with open(config_file_path) as config_file:
                config_data = toml.load(config_file)
            click.echo(f"Retro config for '{target_name}':")
            click.echo(toml.dumps(config_data))  # Display the config
        except FileNotFoundError:
            click.echo(
                f"Error: Config file not found: {config_file_path}\n"
                f"Please run: './retrospector.py init {target_name} <target_repo_path>'"
            )
        except (KeyError, toml.TomlDecodeError, ValidationError) as e:
            click.echo(f"Error reading or validating config file: {e}")
    else:
        run_tests(target_name, iterations)
        analyze_test_results(target_name)


@cli.command()
@click.argument("retro_name")
@click.argument("commit_hash")
def issues(retro_name, commit_hash):
    """Create GitHub issues for failed tests in a specific commit."""
    create_issues_for_commit(retro_name, commit_hash)


if __name__ == "__main__":
    cli()
