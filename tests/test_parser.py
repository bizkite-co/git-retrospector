import unittest
import tempfile
import csv
import os
from git_retrospector.parser import _process_vitest_log, _process_playwright_xml
from git_retrospector.retro import Retro
from TestConfig import BaseTest


class TestParser(BaseTest):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        # Create a basic retro for testing
        self.retro = Retro(
            name="test_target", repo_under_test_path=self.temp_dir.name, output_paths={}
        )
        self.commit_hash = "commit123"
        self.retro.create_commit_hash_dir(self.commit_hash)

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

        vitest_log_path = self.retro.get_vitest_log_path(self.commit_hash)
        with open(vitest_log_path, "w") as vitest_log_file:
            vitest_log_file.write(vitest_log_content)

        # Call _process_vitest_log with the mock file path and retro
        _process_vitest_log(self.retro, vitest_log_path, self.commit_hash)

        # Check that vitest.csv is created
        csv_output_path = self.retro.get_vitest_csv_path(self.commit_hash)

        self.assertTrue(
            self.retro.path_exists(
                os.path.relpath(csv_output_path, self.retro.get_retro_dir())
            )
        )

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

    def test_process_playwright_xml(self):
        # Create a mock Playwright XML file with sample XML content
        playwright_xml_content = """
        <testsuites name="Playwright Tests">
          <testsuite name="Test Suite 1">
            <testcase name="Test Case 1" time="0.123" />
          </testsuite>
        </testsuites>
        """

        playwright_xml_path = self.retro.get_playwright_xml_path(self.commit_hash)
        with open(playwright_xml_path, "w") as playwright_xml_file:
            playwright_xml_file.write(playwright_xml_content)

        # Call _process_playwright_xml with the mock file path and retro
        _process_playwright_xml(self.retro, playwright_xml_path, self.commit_hash)

        # Check that playwright.csv is created
        csv_output_path = self.retro.get_playwright_csv_path(self.commit_hash)
        self.assertTrue(
            self.retro.path_exists(
                os.path.relpath(csv_output_path, self.retro.get_retro_dir())
            )
        )

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


if __name__ == "__main__":
    unittest.main()
