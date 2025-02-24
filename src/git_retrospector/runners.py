#!/usr/bin/env python3
import subprocess
import os


def run_vitest(target_repo, output_dir, config):
    """
    Runs Vitest tests in the target repository.

    Args:
        target_repo (str): The path to the target repository.
        output_dir (str): The directory to store Vitest output.
        config (Config): The configuration object.
    """
    # Use config from parameter
    vitest_output_rel = config.output_paths["vitest"]

    vitest_log_file = os.path.join(output_dir, "vitest.log")
    vitest_output = os.path.join(output_dir, "vitest.xml")
    print("  Running Vitest...")
    with open(vitest_log_file, "w") as vitest_log_file_handle:
        try:
            subprocess.run(
                [
                    "npx",
                    "vitest",
                    "run",
                    "--reporter=junit",
                    f"--outputFile={vitest_output}",
                ],
                cwd=target_repo,  # Run tests in the target repository directory
                stdout=vitest_log_file_handle,
                stderr=subprocess.STDOUT,
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            # vitest returns non-zero exit code on test failure
            print(f"Vitest failed: {e}")  # added to help debug
            pass


def run_playwright(target_repo, output_dir, config):
    """
    Runs Playwright tests in the target repository.

    Args:
        target_repo (str): The path to the target repository.
        output_dir (str): The directory to store Playwright output.
        config (Config): The configuration object.
    """
    playwright_log_file = os.path.join(output_dir, "playwright.log")
    playwright_output = os.path.join(output_dir, "playwright.xml")
    print("  Running Playwright...")
    with open(playwright_log_file, "w") as playwright_log_file_handle:
        try:
            subprocess.run(
                ["npx", "playwright", "test", "--reporter=junit"],
                cwd=target_repo,  # Run tests in the target repository directory
                env={**os.environ, 'PLAYWRIGHT_JUNIT_OUTPUT_NAME': playwright_output, 'PLAYWRIGHT_OUTPUT_DIR': output_dir},
                stdout=playwright_log_file_handle,
                stderr=subprocess.STDOUT,
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            # playwright returns non-zero exit code on test failure
            print(f"Playwright failed: {e}")  # added to help debug
            pass
