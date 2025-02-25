#!/usr/bin/env python3
import os
import subprocess


def run_vitest(target_repo, output_dir, config):
    """
    Runs Vitest tests in the target repository.

    Args:
        target_repo (str): The path to the target repository.
        output_dir (str): The directory to store Vitest output.
        config (Config): The configuration object.
    """
    vitest_log_file = os.path.join(output_dir, "vitest.log")
    # print("  Running Vitest...")
    with open(vitest_log_file, "w") as vitest_log_file_handle:
        try:
            subprocess.run(
                ["npx", "vitest", "run", "--reporter=junit"],
                cwd=target_repo,  # Run tests in the target repository directory
                stdout=vitest_log_file_handle,
                stderr=subprocess.STDOUT,
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            # vitest returns non-zero exit code on test failure
            # print(f"Vitest failed: {e}")  # added to help debug
            pass


def run_playwright(target_repo, output_dir, config):
    """
    Runs Playwright tests in the target repository.

    Args:
        target_repo (str): The path to the target repository.
        output_dir (str): The directory to store the log file.
        config (Config): The configuration object.
    """
    playwright_log_file = os.path.join(output_dir, "playwright.log")
    # print("  Running Playwright...")
    with open(playwright_log_file, "w") as playwright_log_file_handle:
        try:
            subprocess.run(
                ["npx", "playwright", "test", "--reporter=junit"],
                cwd=target_repo,  # Run tests in the target repository directory
                stdout=playwright_log_file_handle,
                stderr=subprocess.STDOUT,
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            # playwright returns non-zero exit code on test failure
            # print(f"Playwright failed: {e}")  # added to help debug
            pass
