import unittest
import tempfile
import os
import csv
from git_retrospector.parser import _process_vitest_log, _process_playwright_xml


class TestParser(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_process_vitest_log(self):
        # Create a mock Vitest log file with sample XML content
        vitest_log_content = """
        Some log lines before the XML
        <testsuites name="Vitest Tests">
          <testsuite name="Test Suite 1">
            <testcase name="Test Case 1" time="0.123" />
          </testsuite>
        </testsuites>
        Some log lines after the XML
        """
        # Create a temporary directory for the commit
        commit_dir_path = os.path.join(self.temp_dir.name, "commit123")
        os.makedirs(commit_dir_path)
        tool_summary_dir = os.path.join(commit_dir_path, "tool-summary")
        os.makedirs(tool_summary_dir)

        with tempfile.NamedTemporaryFile(
            delete=False, mode="w", dir=tool_summary_dir
        ) as vitest_log_file:
            vitest_log_path = vitest_log_file.name
            vitest_log_file.write(vitest_log_content)

        # Call _process_vitest_log with the mock file path
        _process_vitest_log(vitest_log_path, commit_dir_path)

        # Check that vitest.csv is created
        csv_output_path = os.path.join(tool_summary_dir, "vitest.csv")
        self.assertTrue(os.path.exists(csv_output_path))

        # Read and check the content of vitest.csv (optional, but good practice)
        with open(csv_output_path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
            self.assertEqual(len(rows), 2)  # Header + 1 test case
            self.assertEqual(
                rows[0],
                [
                    "Commit",
                    "Test Type",
                    "Test Name",
                    "Result",
                    "Duration",
                    "Media Path",
                ],
            )
            self.assertEqual(
                rows[1], ["commit123", "vitest", "Test Case 1", "passed", "0.123", ""]
            )

        # Clean up the temporary file and directory
        os.remove(vitest_log_path)

    def test_process_playwright_xml(self):
        # Create a mock Playwright XML file with sample XML content
        playwright_xml_content = """
        <testsuites name="Playwright Tests">
          <testsuite name="Test Suite 1">
            <testcase name="Test Case 1" time="0.123" />
          </testsuite>
        </testsuites>
        """
        # Create a temporary directory for the commit
        commit_dir_path = os.path.join(self.temp_dir.name, "commit123")
        os.makedirs(commit_dir_path)
        tool_summary_dir = os.path.join(commit_dir_path, "tool-summary")
        os.makedirs(tool_summary_dir)

        with tempfile.NamedTemporaryFile(
            delete=False, mode="w", dir=tool_summary_dir
        ) as playwright_xml_file:  # specify dir
            playwright_xml_path = playwright_xml_file.name
            playwright_xml_file.write(playwright_xml_content)

        # Call _process_playwright_xml with the mock file path and a temporary directory
        _process_playwright_xml(playwright_xml_path, commit_dir_path)

        # Check that playwright.csv is created
        csv_output_path = os.path.join(tool_summary_dir, "playwright.csv")
        self.assertTrue(os.path.exists(csv_output_path))

        # Read and check the content of playwright.csv (optional, but good practice)
        with open(csv_output_path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
            self.assertEqual(len(rows), 2)  # Header + 1 test case
            self.assertEqual(
                rows[0],
                [
                    "Commit",
                    "Test Type",
                    "Test Name",
                    "Result",
                    "Duration",
                    "Media Path",
                ],
            )
            self.assertEqual(
                rows[1],
                ["commit123", "playwright", "Test Case 1", "passed", "0.123", ""],
            )
        # Clean up the temporary file
        os.remove(playwright_xml_path)


if __name__ == "__main__":
    unittest.main()
