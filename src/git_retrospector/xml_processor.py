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
    csv_writer.writerow([commit, test_type, name, result, f"{time:.3f}", media_path])


def _process_test_suite(test_suite, commit, test_type, csv_writer):
    """Processes a single test suite and extracts test case data."""
    for test_case in test_suite.findall("./testcase"):
        name = f"{test_case.get('classname')}::{test_case.get('name')}"
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

        _write_test_case_to_csv(
            csv_writer, commit.name, test_type, name, result, time, media_path
        )


def process_xml_string(
    xml_string: str, commit: str, test_type: str, csv_writer: Optional[Any] = None
):
    """Processes a string containing XML test results and writes data to CSV files.

    Args:
        xml_string: The XML content as a string.
        commit: The commit hash associated with the test results.
        test_type: The type of test (e.g., 'vitest', 'playwright').
        csv_writer: CSV writer
    """
    try:
        root = ET.fromstring(xml_string)

        # Handle both top-level 'testsuites' and 'testsuite'
        if root.tag == "testsuites":
            test_suites = root.findall("./testsuite")
        elif root.tag == "testsuite":
            test_suites = [root]
        else:
            return  # Skip if the root tag is unexpected

        for test_suite in test_suites:
            _process_test_suite(test_suite, commit, test_type, csv_writer)

    except ET.ParseError:
        return  # Don't write to CSV if there's a parsing error
    except Exception:
        pass
