#!/usr/bin/env python3
import argparse
import os
import shutil  # Import the shutil module
import subprocess
from pathlib import Path

import toml
from pydantic import ValidationError

from git_retrospector.config import Config  # Import the Config class
from git_retrospector.git_utils import (  # Import Git utility functions
    get_current_commit_hash,
    get_origin_branch_or_commit,
)
from git_retrospector.runners import (  # Import test runner functions
    run_playwright,
    run_vitest,
)


def process_commit(target_repo, commit_hash, output_dir, origin_branch, config):
    """
    Checks out a specific commit in the target repository, runs tests, and
    returns to the original branch.

    Args:
        target_repo (str): The path to the target repository.
        commit_hash (str): The hash of the commit to process.
        output_dir (str): The base output directory.
        origin_branch (str): The original branch to return to.
        config (Config): The configuration object.
    """
    output_dir_for_commit = config.test_result_dir / "test-output" / commit_hash
    output_dir_for_commit.mkdir(parents=True, exist_ok=True)

    if origin_branch is None:
        return

    try:
        subprocess.run(
            ["git", "checkout", "--force", commit_hash],
            cwd=target_repo,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return

    run_vitest(target_repo, str(output_dir_for_commit), config)
    run_playwright(target_repo, str(output_dir_for_commit), config)

    # Move Playwright output to the correct location
    try:
        source_dir = Path(target_repo) / "test-results"
        if source_dir.exists():
            for item in os.listdir(source_dir):
                s = os.path.join(source_dir, item)
                d = os.path.join(output_dir_for_commit, item)
                if os.path.isdir(s):
                    shutil.move(s, d)
                else:
                    shutil.move(s, d)
            shutil.rmtree(source_dir)  # Remove the source directory after moving

        # Rename playwright.log to playwright.xml
        playwright_log_path = os.path.join(output_dir_for_commit, "playwright.log")
        playwright_xml_path = os.path.join(output_dir_for_commit, "playwright.xml")
        if os.path.exists(playwright_log_path):
            os.rename(playwright_log_path, playwright_xml_path)

    except Exception:
        pass

    try:
        subprocess.run(
            ["git", "checkout", "--force", origin_branch],
            cwd=target_repo,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return


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

    except (FileNotFoundError, KeyError, toml.TomlDecodeError):
        return
    except ValidationError:
        return

    commits_log_path = config.test_result_dir / "commits.log"
    with open(commits_log_path, "w") as commits_log:
        origin_branch = get_origin_branch_or_commit(target_repo)

        # Check if target_repo is a git repository
        assert origin_branch is not None, (
            "Error: Target repo directory {target_repo} is not a git repository "
            "or does not exist"
        )

        for i in range(iteration_count):
            try:
                # Use get_current_commit_hash to get the initial HEAD
                current_commit = get_current_commit_hash(target_repo)
                if current_commit is None:
                    return

                commit_hash_result = subprocess.run(
                    ["git", "rev-parse", "--short", f"{current_commit}~{i}"],
                    cwd=target_repo,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                commit_hash = commit_hash_result.stdout.strip()
                if not commit_hash:
                    continue  # Skip this iteration
                process_commit(
                    target_repo, commit_hash, test_output_dir, origin_branch, config
                )
                commits_log.write(f"{commit_hash}\n")

            except subprocess.CalledProcessError:
                continue


def initialize(target_name, repo_under_test_path, output_base_dir="retros"):
    """
    Initializes the target-specific directory and config file.

    Args:
        target_name (str): The name of the target repository.
        repo_under_test_path (str): The path to the target repository.
        output_base_dir (str, optional): The base directory for retrospectives.
            Defaults to "retros".
    """
    config_file_path = os.path.join(output_base_dir, target_name, "config.toml")
    if not os.path.exists(config_file_path):
        config = Config(
            name=target_name,
            repo_under_test_path=repo_under_test_path,
            test_result_dir=os.path.join(output_base_dir, target_name),
            output_paths={
                "vitest": "test-output/vitest.xml",
                "playwright": "test-output/playwright.xml",
            },
        )
        config.print_full_paths()  # Print the full paths
        # Convert Path objects to strings for TOML serialization
        config_data = config.model_dump()
        config_data["repo_under_test_path"] = str(config_data["repo_under_test_path"])
        config_data["test_result_dir"] = str(config_data["test_result_dir"])

        with open(config_file_path, "w") as config_file:
            toml.dump(config_data, config_file)  # Use config_data
    return config_file_path


def analyze_test_results(retro_name):
    """
    Analyzes test results for a given retro.
    """
    from git_retrospector.parser import process_retro  # Import here to

    # avoid circular dependency

    process_retro(retro_name)


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

    args = parser.parse_args()

    if args.command == "init":
        initialize(args.target_name, args.target_repo_path)
    elif args.command == "run":
        run_tests(args.target_name, args.iterations)
        analyze_test_results(args.target_name)
    else:
        parser.print_help()
