import csv
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock

from git_retrospector.xml_processor import (
    _process_test_suite,
    _write_test_case_to_csv,
    extract_media_paths,
    process_xml_string,
)


class TestXMLProcessor(unittest.TestCase):
    def test_extract_media_paths(self):
        # Test case with multiple paths
        cdata1 = (
            "Some text test-results/path/to/file1.png "
            "more text test-results/path/to/file2.webm"
        )
        expected1 = "test-results/path/to/file1.png;test-results/path/to/file2.webm"
        self.assertEqual(extract_media_paths(cdata1), expected1)

        # Test case with no paths
        cdata2 = "Some text without any paths"
        expected2 = ""
        self.assertEqual(extract_media_paths(cdata2), expected2)

        # Test case with a single path
        cdata3 = "test-results/path/to/file3.zip"
        expected3 = "test-results/path/to/file3.zip"
        self.assertEqual(extract_media_paths(cdata3), expected3)

        # Test case with mixed slashes
        cdata4 = (
            "test-results/path/to/file4.png\\nand then "
            "test-results/another_path/file5.jpg"
        )
        self.assertEqual(extract_media_paths(cdata4), "test-results/path/to/file4.png")

    def test_write_test_case_to_csv(self):
        mock_csv_writer = MagicMock()
        commit = "commit123"
        test_type = "vitest"
        name = "test_case_1"
        result = "passed"
        time = 0.123
        media_path = "path/to/media.png"

        _write_test_case_to_csv(
            mock_csv_writer, commit, test_type, name, result, time, media_path
        )

        mock_csv_writer.writerow.assert_called_once_with(
            [commit, test_type, name, result, time, media_path]
        )

    def test_process_test_suite(self):
        # Create a mock testsuite XML element
        test_suite_xml = """
        <testsuite name="Suite1">
            <testcase name="test1" time="0.1">
                <failure>Failure message</failure>
            </testcase>
            <testcase name="test2" time="0.2" />
            <testcase name="test3" time="0.3">
                <skipped/>
            </testcase>
        </testsuite>
        """
        test_suite = ET.fromstring(test_suite_xml)
        commit = "commit123"
        test_type = "pytest"
        mock_csv_writer = MagicMock()

        _process_test_suite(test_suite, commit, test_type, mock_csv_writer)

        # Assert that _write_test_case_to_csv was called three times with
        # the correct arguments
        self.assertEqual(mock_csv_writer.writerow.call_count, 3)
        mock_csv_writer.writerow.assert_any_call(
            [commit, test_type, "test1", "failed", 0.1, ""]
        )
        mock_csv_writer.writerow.assert_any_call(
            [commit, test_type, "test2", "passed", 0.2, ""]
        )
        mock_csv_writer.writerow.assert_any_call(
            [commit, test_type, "test3", "skipped", 0.3, ""]
        )

    def test_process_xml_string(self):
        # Create a mock XML string
        xml_string = """
        <testsuites>
            <testsuite name="Suite1">
                <testcase name="test1" time="0.1" />
            </testsuite>
            <testsuite name="Suite2">
                <testcase name="test2" time="0.2" />
                <testcase name="test3" time="0.3" />
            </testsuite>
        </testsuites>
        """
        commit = "commit123"
        test_type = "pytest"

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_output_path = os.path.join(temp_dir, f"temp_{test_type}_{commit}.csv")
            with open(csv_output_path, "w", newline="") as individual_csvfile:
                csv_writer = csv.writer(individual_csvfile)
                process_xml_string(xml_string, commit, test_type, csv_writer)

            # check the file was created and has content
            self.assertTrue(os.path.exists(csv_output_path))
            with open(csv_output_path) as f:
                content = f.read()
            self.assertIn("test1", content)
            self.assertIn("test2", content)
            self.assertIn("test3", content)


if __name__ == "__main__":
    unittest.main()
