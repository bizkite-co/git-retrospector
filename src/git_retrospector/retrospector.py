#!/usr/bin/env python3
import csv
import logging
import subprocess
import sys
import os  # Import the os module
from pathlib import Path
import time
import xml.etree.ElementTree as ET
import json

import click
from github import Github, GithubException
from pydantic import ValidationError
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML

from git_retrospector.commit_processor import process_commit
from git_retrospector.retro import Retro
from git_retrospector.git_utils import (
    get_current_commit_hash,
    get_origin_branch_or_commit,
    ensure_screenshots_branch,
)
from git_retrospector.parser import process_retro  # Import process_retro

import toml
import coloredlogs

# Configure logging
coloredlogs.install(level="INFO", fmt="%(message)s")


def get_error_details_from_junit(commit_dir, test_name, retro):
    """
    Extracts the error message and stack trace from the playwright.xml file
    for a specific failed test.

    Args:
        commit_dir: The directory for the specific commit.
        test_name:  The name of the test.
        retro: The Retro object

    Returns:
        A tuple containing (error_message, stack_trace), or (None, None) if not found.
    """
    try:
        # Construct path to the JUnit XML file
        junit_xml_path = os.path.join(commit_dir, "tool-summary", "playwright.xml")

        if not os.path.exists(junit_xml_path):
            logging.warning(f"JUnit XML file not found: {junit_xml_path}")
            return None, None

        tree = ET.parse(junit_xml_path)
        root = tree.getroot()

        for testcase in root.findall(".//testcase"):
            # Match the test name.  The CSV file has extra info after the name,
            # so we use 'startswith'
            if testcase.get("name").startswith(test_name):
                failure = testcase.find("failure")
                if failure is not None:
                    message = failure.get("message")
                    stack_trace = failure.text
                    return message, stack_trace
                error = testcase.find("error")
                if error is not None:
                    message = error.get("message")
                    stack_trace = error.text
                    return message, stack_trace
    except ET.ParseError as e:
        logging.error(f"Error parsing JUnit XML: {e}")
        return None, None

    return None, None


def process_single_commit(
    target_repo, commit_hash, test_output_dir, origin_branch, retro
):
    """Processes a single commit."""
    try:
        process_commit(
            retro.remote_repo_path,
            commit_hash,
            test_output_dir,
            origin_branch,
            retro,
        )
        time.sleep(1)  # Added delay
        os.sync()

        # Check if the commit output directory exists before listing contents
        commit_output_dir = retro.get_test_output_dir(commit_hash)
        if commit_output_dir.exists():
            logging.debug(
                f"""Contents of {commit_output_dir}: {
                    list(commit_output_dir.glob('*'))
                }"""
            )
            logging.debug(
                f"""Contents of {commit_output_dir} using os.listdir: {
                    os.listdir(commit_output_dir)
                    }"""
            )
        else:
            logging.warning(
                f"Commit output directory does not exist: {commit_output_dir}"
            )

    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing commit {commit_hash}: {e}")


def run_tests(target_name, iteration_count, keep=False):
    """
    Runs tests on a range of commits in the target repository.

        target_name (str): The name of the target repository (used to locate the
            retro file).
        iteration_count (int): The number of commits to go back in history.
        keep (bool): Whether to keep the checked out commit.
    """
    # Load retro
    config_file_path = os.path.join("retros", target_name, "retro.toml")
    try:
        with open(config_file_path) as config_file:
            config_data = toml.load(config_file)
        retro = Retro(**config_data)
        target_repo = str(retro.remote_repo_path)  # Renamed
        test_output_dir = str(retro.local_test_output_dir_full)
    except FileNotFoundError:
        click.echo(
            f"Error: Retro file not found: {config_file_path}\n"
            f"Please run: './retrospector.py init {target_name} <target_repo_path>'"
        )
        logging.error(f"Retro file not found: {config_file_path}")
        return
    except (KeyError, toml.TomlDecodeError) as e:
        logging.error(f"Error reading retro file: {e}")
        return
    except ValidationError as e:
        logging.error(f"Error validating retro file: {e}")
        return

    commits_log_path = Path(retro.get_test_output_dir()) / "commits.log"
    with open(commits_log_path, "w") as commits_log:
        origin_branch = get_origin_branch_or_commit(target_repo)

        # Check if target_repo is a git repository
        assert origin_branch is not None, (
            "Error: Target repo directory {target_repo} is not a git "
            "repository or does not exist"
        )

        logging.info(f"Running tests for {target_name} ({iteration_count} iterations)")

        # Create the base test-output directory
        os.makedirs(retro.get_test_output_dir(), exist_ok=True)

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

                process_single_commit(
                    target_repo, commit_hash, test_output_dir, origin_branch, retro
                )

                commits_log.write(f"{commit_hash}\n")
            except subprocess.CalledProcessError as e:
                logging.error(f"Error processing commit {current_commit}~{i}: {e}")
                continue

        if not keep:
            try:
                subprocess.run(
                    ["git", "checkout", "--force", origin_branch],
                    cwd=target_repo,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logging.error(f"Error during git checkout {origin_branch}: {e}")
                return


def analyze_test_results(retro):
    """
    Analyzes test results for a given retro. Now accepts a retro object.
    """
    process_retro(retro)


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
    config_file_path = os.path.join("retros", retro_name, "retro.toml")
    with open(config_file_path) as config_file:
        config_data = toml.load(config_file)
    retro = Retro(**config_data)
    return retro


def get_user_confirmation(failed_count):
    """Gets user confirmation to proceed with creating issues."""
    while True:
        user_input = prompt(
            HTML(
                f"""<style bg="ansiyellow" fg="black">Found {
                    failed_count
                } failed tests.</style> """
                f'<style fg="ansicyan">Create GitHub issues? (y/n): </style>'
            )
        ).lower()
        if user_input in ["y", "n"]:
            return user_input == "y"


def get_screenshot_url(row, commit_dir, retro):
    """
    Extracts and uploads the screenshot for a failed test, returning the URL.
    """
    media_paths = row.get("Media Path", "").split(";")
    for media_path in media_paths:
        # Check if the file is an image or video
        if media_path.lower().endswith(
            (".png", ".jpg", ".jpeg", ".gif", ".mp4", ".webm")
        ):
            # Construct the full path.  Remove 'test-results/' prefix if present
            relative_path = media_path.replace("test-results/", "", 1)
            full_media_path = os.path.join(commit_dir, relative_path)

            # Upload the screenshot if found and get URL
            screenshot_url = upload_screenshot_to_github(
                full_media_path, retro.github_repo_owner, retro.github_repo_name
            )
            if screenshot_url:
                return screenshot_url  # Stop after the first successful upload
    return None


def construct_issue_body(test_name, error_message, stack_trace, screenshot_url):
    """Constructs the GitHub issue body."""
    body = f"**Test Name:** {test_name}\n\n"
    if error_message:
        body += f"**Error:** {error_message}\n\n"
    if stack_trace:
        body += f"**Stack Trace:**\n```\n{stack_trace}\n```\n"
    if screenshot_url:
        body += f"**Screenshot/Video:**\n![Screenshot]({screenshot_url})\n"
    return body


def process_csv_files(
    repo, playwright_csv, vitest_csv, existing_issues, commit_dir, retro
):
    """Processes CSV files, uploads screenshots, and creates issues for failed tests."""
    logging.info(
        "process_csv_files called with repo: %s, playwright_csv: %s, vitest_csv: %s",
        repo,
        playwright_csv,
        vitest_csv,
    )
    existing_titles = {issue.title for issue in existing_issues}

    for csv_file in [playwright_csv, vitest_csv]:
        if csv_file:
            with open(csv_file) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Result") == "failed":
                        test_name = row.get("Test Name", "Unnamed Test")
                        if test_name in existing_titles:
                            logging.info(
                                f"Skipping issue creation, "
                                f"title already exists: {test_name}"
                            )
                            continue

                        # Get the media paths from the CSV row and upload screenshot
                        screenshot_url = get_screenshot_url(row, commit_dir, retro)

                        # Load error details from JSON (if available)
                        error_message = None
                        stack_trace = None
                        errors_json_path = os.path.join(
                            commit_dir, "tool-summary", "errors.json"
                        )
                        if os.path.exists(errors_json_path):
                            try:
                                with open(errors_json_path) as errors_file:
                                    errors_data = json.load(errors_file)
                                    error_info = errors_data.get(test_name)
                                    if error_info:
                                        error_message = error_info.get("error")
                                        stack_trace = error_info.get("stack_trace")
                            except Exception as e:
                                logging.error(
                                    f"Error loading or parsing errors.json: {e}"
                                )

                        # Construct the issue body
                        body = construct_issue_body(
                            test_name, error_message, stack_trace, screenshot_url
                        )

                        logging.info(f"Creating issue with title: {test_name}")
                        repo.create_issue(title=test_name, body=body)


def should_create_issues(retro_name, commit_hash):
    """Checks if conditions are met to create GitHub issues."""
    logging.info(
        f"""should_create_issues called with retro_name: {
            retro_name
            }, commit_hash: {commit_hash}"""
    )
    commit_dir = os.path.join("retros", retro_name, "test-output", commit_hash)
    if not os.path.exists(commit_dir):
        logging.info(f"Commit directory does not exist: {commit_dir}")
        return False

    try:
        playwright_csv, vitest_csv = find_test_summary_files(commit_dir)
    except FileNotFoundError as e:
        logging.info(f"Error finding test summary files: {e}")
        return False

    if not playwright_csv and not vitest_csv:
        logging.info("No CSV files found")
        return False

    failed_count = 0
    for csv_file in [playwright_csv, vitest_csv]:
        if csv_file:
            count = count_failed_tests(csv_file)
            if count == -1:
                logging.info(f"Error reading CSV file: {csv_file}")
                return False  # Stop if there was an error reading a file
            failed_count += count

    if failed_count == 0:
        logging.info("No failed tests found")
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


def create_github_issues(
    repo_owner, repo_name, playwright_csv, vitest_csv, commit_dir, retro
):
    """Creates GitHub issues based on failed test data, avoiding duplicates."""
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        return

    g = Github(token)

    try:
        repo = g.get_user(repo_owner).get_repo(repo_name)
        existing_issues = list(repo.get_issues(state="open"))  # Get open issues
    except Exception as e:
        logging.error(f"Error getting repository {repo_owner}/{repo_name}: {e}")
        return

    # Ensure the screenshots branch exists
    if not ensure_screenshots_branch(retro.remote_repo_path):
        logging.error("Could not ensure screenshots branch exists.")
        return

    process_csv_files(
        repo, playwright_csv, vitest_csv, existing_issues, commit_dir, retro
    )


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
        logging.info(f"upload_path: {upload_path}")

        try:
            # Check if the file already exists
            repo.get_contents(upload_path, ref="test-screenshots")
            logging.warning(f"Screenshot already exists at {upload_path}")
            return (
                f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}"
                f"/test-screenshots/{upload_path}"
            )
        except GithubException as e:
            if e.status == 404:  # File does not exist, proceed with upload
                repo.create_file(
                    upload_path,
                    f"Upload screenshot {screenshot_name}",
                    content,
                    branch="test-screenshots",
                )
                return (
                    f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}"
                    f"/test-screenshots/{upload_path}"
                )  # Raw URL
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
    logging.info(
        "create_issues_for_commit called with retro_name: "
        f"{retro_name}, commit_hash: {commit_hash}"
    )
    if not should_create_issues(retro_name, commit_hash):
        logging.warning(
            f"Commit {commit_hash} does not exist on the '{retro_name}' repo."
        )
        return

    retro: Retro = load_config_for_retro(retro_name)
    if not retro.github_repo_owner or not retro.name:
        logging.info(f"Could not load repo owner or name for {retro_name}")
        return

    commit_dir = os.path.join("retros", retro_name, "test-output", commit_hash)
    playwright_csv, vitest_csv = find_test_summary_files(commit_dir)
    create_github_issues(
        retro.github_repo_owner,
        retro.github_repo_name,
        playwright_csv,
        vitest_csv,
        commit_dir,
        retro,
    )


def handle_no_command():
    command_completer = WordCompleter(
        ["init", "run", "issues", "parse"], ignore_case=True
    )
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
        elif command_name == "parse":  # Add handling for the 'parse' command
            handle_parse_command(command_parts)
        else:
            click.echo(f"Unknown command: {command_name}")


def handle_init_command(command_parts):
    if len(command_parts) == 3:
        target_name = command_parts[1]
        remote_repo_path = command_parts[2]  # Renamed
        init(target_name, remote_repo_path)  # Renamed
    else:
        click.echo("Usage: init <target_name> <target_repo_path>")


def handle_run_command(command_parts):
    if len(command_parts) >= 2:
        target_name = command_parts[1]
        #  Handle optional arguments for run
        iterations = 10
        if "-i" in command_parts:
            try:
                iterations_index = command_parts.index("-i") + 1
                iterations = int(command_parts[iterations_index])
            except (ValueError, IndexError):
                click.echo("Invalid value for iterations.")
                return
        if "-c" in command_parts:
            try:
                # Removed unused variable assignment and index operation:
                command_parts.index("-c")
            except IndexError:
                click.echo("Invalid value for commit_dir")
                return
        if "-k" in command_parts or "--keep" in command_parts:
            keep = True
        else:
            keep = False
        run_tests(target_name, iterations, keep)

    else:
        click.echo(
            "Usage: run <target_name> [-i iterations] [-c commit_dir] [-k/--keep]"
        )


def handle_issues_command(command_parts):
    if len(command_parts) == 3:
        retro_name = command_parts[1]
        commit_hash = command_parts[2]
        issues(retro_name, commit_hash)
    else:
        click.echo("Usage: issues <retro_name> <commit_hash>")


def handle_parse_command(command_parts):  # New function to handle 'parse'
    if len(command_parts) == 2:
        retro_name = command_parts[1]
        config_file_path = os.path.join("retros", retro_name, "retro.toml")
        try:
            with open(config_file_path) as config_file:
                config_data = toml.load(config_file)
            retro = Retro(**config_data)
            process_retro(retro)  # Pass the retro object
        except FileNotFoundError:
            click.echo(f"Error: Retro file not found: {config_file_path}")
        except (KeyError, toml.TomlDecodeError, ValidationError) as e:
            click.echo(f"Error reading or validating retro file: {e}")
    else:
        click.echo("Usage: parse <retro_name>")


@click.group()
def cli():
    """Run tests on a range of commits and parse results."""
    if not os.environ.get("TEST_ENVIRONMENT") and not any(
        arg in sys.argv for arg in ["init", "run", "issues", "parse"]
    ):
        handle_no_command()


@cli.command()
@click.argument("target_name")
@click.argument("remote_repo_path")  # Renamed
def init(target_name, remote_repo_path):  # Renamed
    """Initialize a target repository."""
    try:
        # Get project root from environment variable if available, otherwise use git
        project_root = os.environ.get("PROJECT_ROOT")
        logging.info(f"init: PROJECT_ROOT from env: {project_root}")
        if not project_root:
            project_root = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            logging.info(f"init: project_root from git: {project_root}")
        Retro.initialize(
            target_name,
            remote_repo_path,
            project_root,
            github_remote="",
            github_repo_name="",
            github_repo_owner="",
            github_project_name="",
            github_project_number=0,
            github_project_owner="",
            test_result_dir="",
            test_runners=[],
        )  # Renamed and added parameters
    except subprocess.CalledProcessError:
        raise click.ClickException(
            "Not in a git repository. Run 'git init' in your project root."
        ) from None
    except ValueError as e:
        raise click.ClickException(str(e)) from None


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
@click.option(
    "-k", "--keep", is_flag=True, help="Keep checked out commit after running tests"
)
def run(target_name, iterations, commit_dir, keep):
    """Run tests on a target repository."""
    if not any(arg in sys.argv for arg in ["-i", "--iterations", "-c", "--commit_dir"]):
        config_file_path = os.path.join("retros", target_name, "retro.toml")
        try:
            with open(config_file_path) as config_file:
                config_data = toml.load(config_file)
            retro = Retro(**config_data)
            click.echo(f"Retro retro for '{target_name}':")
            click.echo(toml.dumps(config_data))  # Display the retro
        except FileNotFoundError:
            click.echo(
                f"Error: Retro file not found: {config_file_path}\n"
                f"Please run: './retrospector.py init {target_name} <target_repo_path>'"
            )
            return  # Added return
        except (KeyError, toml.TomlDecodeError, ValidationError) as e:
            click.echo(f"Error reading or validating retro file: {e}")
            return  # Added return
    else:
        config_file_path = os.path.join("retros", target_name, "retro.toml")
        try:
            with open(config_file_path) as config_file:
                config_data = toml.load(config_file)
            retro = Retro(**config_data)
        except (
            FileNotFoundError,
            KeyError,
            toml.TomlDecodeError,
            ValidationError,
        ) as e:
            click.echo(f"Error loading retro: {e}")
            return
        # Create the base test-output directory
        os.makedirs(retro.get_test_output_dir(), exist_ok=True)
        run_tests(target_name, iterations, keep)
        analyze_test_results(retro)  # Pass retro


@cli.command()
@click.argument("retro_name")
@click.argument("commit_hash")
def issues(retro_name, commit_hash):
    """Create GitHub issues for failed tests in a specific commit."""
    create_issues_for_commit(retro_name, commit_hash)


@cli.command("parse")  # New 'parse' command
@click.argument("retro_name")
def parse(retro_name):
    """Process test results for a given retro."""
    config_file_path = os.path.join("retros", retro_name, "retro.toml")
    try:
        with open(config_file_path) as config_file:
            config_data = toml.load(config_file)
        retro = Retro(**config_data)
        process_retro(retro)  # Pass the retro object
    except FileNotFoundError:
        click.echo(f"Error: Retro file not found: {config_file_path}")
    except (KeyError, toml.TomlDecodeError, ValidationError) as e:
        click.echo(f"Error reading or validating retro file: {e}")


if __name__ == "__main__":
    cli()
