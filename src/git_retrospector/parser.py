#!/usr/bin/env python3
import csv
import logging
import os


from git_retrospector import xml_processor  # Import the updated module
from git_retrospector.retro import Retro  # Use new class name


def _process_vitest_xml(retro: Retro, vitest_xml_path, commit_hash):
    """Processes a Vitest XML file and extracts test results."""
    try:
        # Check if the file exists before trying to open it
        if not os.path.exists(vitest_xml_path):
            logging.warning(f"Vitest XML file not found: {vitest_xml_path}")
            return

        with open(vitest_xml_path) as vitest_xml_file:
            vitest_xml_string = vitest_xml_file.read()
            csv_output_path = retro.get_vitest_csv_path(commit_hash)
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
                    commit_hash,  # Use commit_hash directly
                    "vitest",
                    csv_writer,
                )

    except Exception as e:
        logging.error(f"Error processing Vitest XML file {vitest_xml_path}: {e}")


def _process_playwright_xml(retro: Retro, playwright_xml_path, commit_hash):
    """Processes a Playwright XML file and extracts test results."""
    logging.info(f"Processing Playwright XML: {playwright_xml_path}")
    try:
        # Check if the file exists before trying to open it
        if not os.path.exists(playwright_xml_path):
            logging.warning(f"Playwright XML file not found: {playwright_xml_path}")
            return

        with open(playwright_xml_path) as playwright_xml_file:
            playwright_xml_string = playwright_xml_file.read()
            csv_output_path = retro.get_playwright_csv_path(commit_hash)
            logging.info(f"Writing Playwright CSV to: {csv_output_path}")
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
                    commit_hash,  # Use commit_hash directly
                    "playwright",
                    csv_writer,
                )
    except Exception as e:
        logging.error(
            f"ERROR processing Playwright XML file {playwright_xml_path}: {e}"
        )


def parse_commit_results(retro: Retro, commit_hash: str):
    """
    Parses test results from XML files (for Vitest and Playwright)
    in a specified commit directory and writes summaries to CSV files.

        retro (Retro): The configuration object.
        commit_hash (str): The hash of the commit to parse results for.
    """
    # XML files are in the commit dir, *next* to tool-summary
    vitest_xml_path = retro.get_vitest_xml_path(commit_hash)
    playwright_xml_path = retro.get_playwright_xml_path(commit_hash)

    # Process Vitest XML
    logging.info(f"Checking for Vitest XML at: {vitest_xml_path}")
    if retro.path_exists(vitest_xml_path):
        logging.info(
            f"Vitest XML found, processing: {vitest_xml_path}"
        )  # Added logging
        _process_vitest_xml(retro, vitest_xml_path, commit_hash)
    else:
        logging.error(f"Vitest XML file not found: {vitest_xml_path}")

    # Process Playwright XML
    if retro.path_exists(playwright_xml_path):
        _process_playwright_xml(retro, playwright_xml_path, commit_hash)
    else:
        logging.error(f"Playwright XML file not found: {playwright_xml_path}")


def process_retro(retro: Retro):
    """
    Processes all commits within a retro's test output directory.

    Args:
        retro (Retro): The configuration object.
    """
    for commit_hash in retro.list_commit_dirs():
        parse_commit_results(retro, commit_hash)
