#!/usr/bin/env python3
import argparse
import csv
import os
import re  # Import the regular expression module
import sys

from git_retrospector import xml_processor  # Import the updated module


def _process_vitest_log(vitest_log_path, commit_dir, csv_writer):
    """Processes a Vitest log file and extracts test results."""
    try:
        with open(vitest_log_path) as vitest_log_file:
            log_content = vitest_log_file.read()
            # Extract XML content using regex
            match = re.search(r"<testsuites.+?</testsuites>", log_content, re.DOTALL)
            if match:
                vitest_xml_string = match.group(0)
                xml_processor.process_xml_string(
                    vitest_xml_string, commit_dir, "vitest", csv_writer
                )
            else:
                # print(f"Warning: No XML content found in {vitest_log_path}")
                pass

    except Exception:
        # print(f"Error processing Vitest log file {vitest_log_path}: {e}")
        pass


def _process_playwright_xml(playwright_xml_path, commit_dir, csv_writer):
    """Processes a Playwright XML file and extracts test results."""
    try:
        with open(playwright_xml_path) as playwright_xml_file:
            playwright_xml_string = playwright_xml_file.read()
        xml_processor.process_xml_string(
            playwright_xml_string, commit_dir, "playwright", csv_writer
        )
    except Exception:
        # print(
        #     f"Error processing Playwright XML file {playwright_xml_path}: {e}"
        # )
        pass


def parse_test_results(commit_dir=None, results_dir=None):
    """
    Parses test results from log files (for Vitest) and XML files (for Playwright)
    in a specified directory and writes a summary to a CSV file.

        commit_dir (str, optional): If provided, only this commit directory within
            results_dir will be processed. Defaults to None (process all
            commit directories).
        results_dir (str, optional): The directory containing commit-specific test
            results. Defaults to "commit-test-results" in the script's directory.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Determine results_dir
    if results_dir is None:
        results_dir = os.path.join(script_dir, "commit-test-results")  # Default path

    # Determine output_file path
    if results_dir:
        output_file = os.path.join(os.getcwd(), "test_results_summary.csv")  # Use cwd
    else:
        output_file = os.path.join(
            script_dir, "test_results_summary.csv"
        )  # Use script_dir

    with open(output_file, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([
            "Commit",
            "Test Type",
            "Test Name",
            "Result",
            "Duration",
            "Media Path",
        ])

        commit_dirs = []
        if commit_dir:
            if os.path.isdir(os.path.join(results_dir, commit_dir)):
                commit_dirs.append(commit_dir)
            else:
                # print(
                #     f"Error: Specified commit directory '{commit_dir}' not found in '{results_dir}'.",  # noqa: E501
                #     file=sys.stderr,
                # )
                sys.exit(1)  # Keep the exit, but remove the print for the linter.
        else:
            commit_dirs = [
                d
                for d in os.listdir(results_dir)
                if os.path.isdir(os.path.join(results_dir, d))
            ]

        for commit_dir in commit_dirs:
            commit_dir_path = os.path.join(results_dir, commit_dir)

            vitest_log_path = os.path.join(commit_dir_path, "vitest.log")
            playwright_xml_path = os.path.join(commit_dir_path, "playwright.xml")

            # Process Vitest log (extract XML from log)
            if os.path.exists(vitest_log_path):
                _process_vitest_log(vitest_log_path, commit_dir, csv_writer)

            # Process Playwright XML
            if os.path.exists(playwright_xml_path):
                _process_playwright_xml(playwright_xml_path, commit_dir, csv_writer)

    # print(f"Test results summary written to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse test results XML files and generate a summary CSV."
    )
    parser.add_argument(
        "-c", "--commit_dir", help="Specific commit directory to process"
    )
    parser.add_argument(
        "-r", "--results_dir", help="Directory containing the commit directories"
    )
    args = parser.parse_args()

    parse_test_results(args.commit_dir, args.results_dir)
