import argparse
import csv
import re
import xml.etree.ElementTree as ET
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class TestCase(BaseModel):
    name: str = Field(..., alias="name")  # Use alias for XML attribute
    time: float = Field(..., alias="time")
    result: str
    media_path: str = ""


class TestSuite(BaseModel):
    testcases: List[TestCase] = Field(..., alias="testcase")


class TestSuites(BaseModel):
    testsuites: List[TestSuite] = Field(..., alias="testsuite")


def extract_media_paths(failure_cdata: str) -> str:
    """
    Extracts media file paths from the CDATA section of a <failure> tag.

    Args:
        failure_cdata: The string content of the CDATA section.

    Returns:
        A semicolon-separated string of file paths, or an empty string if no
        paths are found.
    """
    # Use a regular expression to find paths in the format
    # 'test-results/.../filename.ext'
    matches = re.findall(
        r"test-results/[a-zA-Z0-9_/-]+\.(?:png|webm|zip)", failure_cdata
    )
    return ";".join(matches)


def _write_test_case_to_csv(
    csv_writer, commit, test_type, name, result, time, media_path
):
    """Writes a single test case's data to the CSV writer."""
    csv_writer.writerow([commit, test_type, name, result, time, media_path])


def _process_test_suite(test_suite, commit, test_type, central_csv_writer):
    """Processes a single test suite and extracts test case data."""
    for test_case in test_suite.findall("./testcase"):
        name = test_case.get("name")
        time_str = test_case.get("time")
        time = float(time_str) if time_str else 0.0

        failures = len(test_case.findall("./failure"))
        errors = len(test_case.findall("./error"))
        skipped = len(test_case.findall("./skipped"))

        if failures > 0 or errors > 0:
            result = "failed"
            # Extract media paths from the <failure> tag's CDATA
            failure_tag = test_case.find("./failure")
            if failure_tag is not None and failure_tag.text:
                media_path = extract_media_paths(failure_tag.text)
            else:
                media_path = ""
        elif skipped > 0:
            result = "skipped"
            media_path = ""  # No media for skipped tests
        else:
            result = "passed"
            media_path = ""  # No media for passed tests

        # Write to individual CSV and central CSV if provided
        _write_test_case_to_csv(
            central_csv_writer, commit, test_type, name, result, time, media_path
        )


def process_xml_string(
    xml_string: str,
    commit: str,
    test_type: str,
    central_csv_writer: Optional[Any] = None,
):
    """
    Processes a string containing XML test results and writes data to CSV files.

    Args:
        xml_string: The XML content as a string.
        commit: The commit hash associated with the test results.
        test_type: The type of test (e.g., 'vitest', 'playwright').
        central_csv_writer: Optional CSV writer for a central CSV file.
    """
    try:
        root = ET.fromstring(xml_string)

        # Determine a base name for output files (use a temporary name)
        base_name = f"temp_{test_type}_{commit}"
        csv_output_path = f"{base_name}.csv"

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

            # Handle both top-level 'testsuites' and 'testsuite'
            if root.tag == "testsuites":
                test_suites = root.findall("./testsuite")
            elif root.tag == "testsuite":
                test_suites = [root]
            else:
                return  # Skip if the root tag is unexpected

            for test_suite in test_suites:
                _process_test_suite(test_suite, commit, test_type, csv_writer)
                if central_csv_writer:
                    _process_test_suite(
                        test_suite, commit, test_type, central_csv_writer
                    )

    except ET.ParseError:
        pass
    except Exception:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process a single XML test results file."
    )
    parser.add_argument(
        "xml_path", help="Path to the XML test results file"
    )  # Keep this for compatibility
    parser.add_argument("commit", help="Commit hash associated with the test results")
    parser.add_argument("test_type", help="Type of test (e.g., 'vitest', 'playwright')")
    args = parser.parse_args()

    # Example of reading from a file (for the example usage)
    with open(args.xml_path) as f:
        xml_content = f.read()
    process_xml_string(xml_content, args.commit, args.test_type)
