import unittest
import os
import csv
import tempfile

from git_retrospector.parser import parse_commit_results


class TestParseCommitResults(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_commit_results(self):
        # Create a temporary directory structure
        commit_dir_path = os.path.join(self.temp_dir.name, "commit_test")
        os.makedirs(commit_dir_path)
        tool_summary_dir = os.path.join(commit_dir_path, "tool-summary")
        os.makedirs(tool_summary_dir)

        # Create dummy playwright.xml file
        playwright_xml_content = """
        <testsuites>
            <testsuite name="Suite1">
                <testcase name="test1" time="0.1" />
                <testcase name="test2" time="0.2">
                    <failure>Error message</failure>
                </testcase>
            </testsuite>
        </testsuites>
        """
        with open(os.path.join(tool_summary_dir, "playwright.xml"), "w") as f:
            f.write(playwright_xml_content)

        # Create dummy vitest.log file
        vitest_log_content = """
        <testsuites>
            <testsuite name="Suite2">
                <testcase name="test3" time="0.3" />
                <testcase name="test4" time="0.4">
                    <failure>Error message</failure>
                </testcase>
            </testsuite>
        </testsuites>
        """
        with open(os.path.join(tool_summary_dir, "vitest.log"), "w") as f:
            f.write(vitest_log_content)

        # Call parse_commit_results
        parse_commit_results(commit_dir_path)

        # Assert that playwright.csv and vitest.csv files were created
        # Assert that playwright.csv and vitest.csv files were created
        self.assertTrue(
            os.path.exists(os.path.join(tool_summary_dir, "playwright.csv"))
        )
        self.assertTrue(os.path.exists(os.path.join(tool_summary_dir, "vitest.csv")))

        # Assert content of playwright.csv
        with open(os.path.join(tool_summary_dir, "playwright.csv")) as f:
            reader = csv.reader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 3)  # Header + 2 test cases
        self.assertEqual(
            rows[0],
            ["Commit", "Test Type", "Test Name", "Result", "Duration", "Media Path"],
        )
        self.assertEqual(
            rows[1],
            [
                os.path.basename(commit_dir_path),
                "playwright",
                "test1",
                "passed",
                "0.1",
                "",
            ],
        )
        self.assertEqual(
            rows[2],
            [
                os.path.basename(commit_dir_path),
                "playwright",
                "test2",
                "failed",
                "0.2",
                "",
            ],
        )

        # Assert content of vitest.csv
        with open(os.path.join(tool_summary_dir, "vitest.csv")) as f:
            reader = csv.reader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 3)  # Header + 2 test cases
        self.assertEqual(
            rows[0],
            ["Commit", "Test Type", "Test Name", "Result", "Duration", "Media Path"],
        )
        self.assertEqual(
            rows[1],
            [os.path.basename(commit_dir_path), "vitest", "test3", "passed", "0.3", ""],
        )
        self.assertEqual(
            rows[2],
            [os.path.basename(commit_dir_path), "vitest", "test4", "failed", "0.4", ""],
        )
