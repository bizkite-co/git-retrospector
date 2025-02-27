#!/usr/bin/env python3
import csv
import os
import re  # Import the regular expression module
import logging

from git_retrospector import xml_processor  # Import the updated module


def _process_vitest_log(vitest_log_path, commit_dir_path):
    """Processes a Vitest log file and extracts test results."""
    try:
        with open(vitest_log_path) as vitest_log_file:
            log_content = vitest_log_file.read()
            # Extract XML content using regex
            match = re.search(r"<testsuites.+?</testsuites>", log_content, re.DOTALL)
            if match:
                vitest_xml_string = match.group(0)
                tool_summary_dir = os.path.join(commit_dir_path, "tool-summary")
                csv_output_path = os.path.join(tool_summary_dir, "vitest.csv")
                with open(csv_output_path, "w", newline="") as individual_csvfile:
                    csv_writer = csv.writer(individual_csvfile)
                    csv_writer.writerow([
                        "Commit",
                        "Test Type",
                        "Test Name",
                        "Result",
                        "Duration",
                        "Media Path",
                    ])
                    xml_processor.process_xml_string(
                        vitest_xml_string,
                        os.path.basename(commit_dir_path),
                        "vitest",
                        csv_writer,
                    )
            else:
                # print(f"Warning: No XML content found in {vitest_log_path}")
                pass

    except Exception:
        # print(f"Error processing Vitest log file {vitest_log_path}: {e}")
        pass


def _process_playwright_xml(playwright_xml_path, commit_dir_path):
    """Processes a Playwright XML file and extracts test results."""
    print(f"Processing Playwright XML: {playwright_xml_path}")  # noqa: T201
    try:
        with open(playwright_xml_path) as playwright_xml_file:
            playwright_xml_string = playwright_xml_file.read()
            tool_summary_dir = os.path.join(commit_dir_path, "tool-summary")
            csv_output_path = os.path.join(tool_summary_dir, "playwright.csv")
            print(f"Writing Playwright CSV to: {csv_output_path}")  # noqa: T201
            with open(csv_output_path, "w", newline="") as individual_csvfile:
                csv_writer = csv.writer(individual_csvfile)
                csv_writer.writerow([
                    "Commit",
                    "Test Type",
                    "Test Name",
                    "Result",
                    "Duration",
                    "Media Path",
                ])
                xml_processor.process_xml_string(
                    playwright_xml_string,
                    os.path.basename(commit_dir_path),
                    "playwright",
                    csv_writer,
                )
    except Exception as e:
        logging.error(
            f"ERROR processing Playwright XML file {playwright_xml_path}: {e}"
        )


def parse_commit_results(commit_dir_path):
    """
    Parses test results from log files (for Vitest) and XML files (for Playwright)
    in a specified commit directory and writes summaries to CSV files.

        commit_dir_path (str): The full path to the commit directory.
    """
    tool_summary_dir = os.path.join(commit_dir_path, "tool-summary")
    vitest_log_path = os.path.join(tool_summary_dir, "vitest.log")
    playwright_xml_path = os.path.join(tool_summary_dir, "playwright.xml")

    # Process Vitest log (extract XML from log)
    if os.path.exists(vitest_log_path):
        _process_vitest_log(vitest_log_path, commit_dir_path)

    # Process Playwright XML
    if os.path.exists(playwright_xml_path):
        _process_playwright_xml(playwright_xml_path, commit_dir_path)


def process_retro(retro_name):
    """
    Processes all commits within a retro's test output directory.

    Args:
        retro_name: The name of the retro (e.g., "handterm").
    """
    retro_dir = os.path.join("retros", retro_name, "test-output")
    for commit_dir in os.listdir(retro_dir):
        commit_dir_path = os.path.join(retro_dir, commit_dir)
        if os.path.isdir(commit_dir_path):
            parse_commit_results(commit_dir_path)
