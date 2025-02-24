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

    vitest_log = os.path.join(output_dir, "vitest.log")
    vitest_output = os.path.join(output_dir, vitest_output_rel)  # Use relative path from config
    print("  Running Vitest...")
    with open(vitest_log, "w") as vitest_log_file:
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
                stdout=vitest_log_file,
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
    # Use config from parameter
    playwright_output_rel = config.output_paths["playwright"]

    playwright_log = os.path.join(output_dir, "playwright.log")
    playwright_output = os.path.join(output_dir, playwright_output_rel)  # Use relative path from config
    print("  Running Playwright...")
    with open(playwright_log, "w") as playwright_log_file:
        try:
            subprocess.run(
                ["npx", "playwright", "test", "--reporter=junit"],
                cwd=target_repo,  # Run tests in the target repository directory
                env={**os.environ, 'PLAYWRIGHT_JUNIT_OUTPUT_NAME': playwright_output},
                stdout=playwright_log_file,
                stderr=subprocess.STDOUT,
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            # playwright returns non-zero exit code on test failure
            print(f"Playwright failed: {e}")  # added to help debug
            pass
