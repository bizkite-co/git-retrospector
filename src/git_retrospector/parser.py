#!/usr/bin/env python3
import os
import csv
import xml.etree.ElementTree as ET
from typing import List, Optional
from pydantic import BaseModel, Field
import argparse
import sys
from git_retrospector.xml_processor import process_xml_file  # Import the function


class TestCase(BaseModel):
    """Represents a single test case with its result and metadata."""
    name: str = Field(..., alias="name")  # Use alias for XML attribute
    time: float = Field(..., alias="time")
    result: str
    media_path: str = ""


class TestSuite(BaseModel):
    """Represents a collection of test cases within a test suite."""
    testcases: List[TestCase] = Field(..., alias="testcase")


class TestSuites(BaseModel):
    """Represents a collection of test suites."""
    testsuites: List[TestSuite] = Field(..., alias="testsuite")


def parse_test_results(commit_dir=None, results_dir=None):
    """
    Parses test results from XML files in a specified directory and writes a summary to a CSV file.

    Args:
        commit_dir (str, optional):  If provided, only this commit directory within results_dir will be processed.
                                     Defaults to None (process all commit directories).
        results_dir (str, optional): The directory containing commit-specific test results.
                                      Defaults to "commit-test-results" in the script's directory.
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
        csv_writer.writerow(
            ["Commit", "Test Type", "Test Name", "Result", "Duration", "Media Path"]
        )

        commit_dirs = []
        if commit_dir:
            if os.path.isdir(os.path.join(results_dir, commit_dir)):
                commit_dirs.append(commit_dir)
            else:
                print(
                    f"Error: Specified commit directory '{commit_dir}' not found in '{results_dir}'.",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            commit_dirs = [
                d
                for d in os.listdir(results_dir)
                if os.path.isdir(os.path.join(results_dir, d))
            ]

        for commit_dir in commit_dirs:
            commit_dir_path = os.path.join(results_dir, commit_dir)

            vitest_xml_path = os.path.join(commit_dir_path, "vitest.xml")
            playwright_xml_path = os.path.join(commit_dir_path, "playwright.xml")

            process_xml_file(vitest_xml_path, commit_dir, "vitest", csv_writer)
            process_xml_file(playwright_xml_path, commit_dir, "playwright", csv_writer)

    print(f"Test results summary written to {output_file}")


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
