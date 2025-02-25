#!/usr/bin/env python3
import argparse
import os
import subprocess

import toml
from pydantic import ValidationError

from git_retrospector.config import Config
from git_retrospector.git_utils import (
    get_current_commit_hash,
    get_origin_branch_or_commit,
)
from git_retrospector.commit_processor import process_commit
from git_retrospector.diff_generator import generate_commit_diffs


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
            "Error: Target repo directory {target_repo} is not a git "
            "repository or does not exist"
        )

        # Use get_current_commit_hash to get the initial HEAD *before* the loop
        current_commit = get_current_commit_hash(target_repo)
        if current_commit is None:
            return

        for i in range(iteration_count):
            try:
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

                print(f"Processing commit: {commit_hash}")  # noqa: T201
                process_commit(
                    target_repo, commit_hash, test_output_dir, origin_branch, config
                )
                commits_log.write(f"{commit_hash}\n")

            except subprocess.CalledProcessError:
                continue


def analyze_test_results(retro_name):
    """
    Analyzes test results for a given retro.
    """
    from git_retrospector.parser import process_retro  # Import here to

    # avoid circular dependency

    process_retro(retro_name)
    generate_commit_diffs(os.path.join("retros", retro_name))


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
        Config.initialize(args.target_name, args.target_repo_path)
    elif args.command == "run":
        run_tests(args.target_name, args.iterations)
        analyze_test_results(args.target_name)
    else:
        parser.print_help()
