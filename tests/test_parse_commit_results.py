import csv
import tempfile
import os
import shutil
from git_retrospector.parser import parse_commit_results
from git_retrospector.retro import Retro
from TestConfig import BaseTest


class TestParseCommitResults(BaseTest):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.retro = Retro(
            name="test_retro", repo_under_test_path=self.temp_dir, output_paths={}
        )
        self.commit_hash = "commit_test"
        # Create the necessary directory structure
        self.retro.create_commit_hash_dir(self.commit_hash)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_parse_commit_results(self):
        # Create dummy playwright.xml file
        playwright_xml_content = """
        <testsuites name="Playwright Tests">
          <testsuite name="Suite1">
            <testcase name="test1" time="0.1" />
            <testcase name="test2" time="0.2">
              <failure>Error message</failure>
            </testcase>
          </testsuite>
        </testsuites>
        """
        with open(self.retro.get_playwright_xml_path(self.commit_hash), "w") as f:
            f.write(playwright_xml_content)

        # Create dummy vitest.log file
        vitest_log_content = """
        <testsuites name="Vitest Tests">
          <testsuite name="Suite2">
            <testcase name="test3" time="0.3" />
            <testcase name="test4" time="0.4">
              <failure>Error message</failure>
            </testcase>
          </testsuite>
        </testsuites>
        """
        with open(self.retro.get_vitest_log_path(self.commit_hash), "w") as f:
            f.write(vitest_log_content)

        # Call parse_commit_results
        parse_commit_results(self.retro, self.commit_hash)

        # Assert that playwright.csv and vitest.csv files were created
        self.assertTrue(
            os.path.exists(self.retro.get_playwright_csv_path(self.commit_hash))
        )
        self.assertTrue(
            os.path.exists(self.retro.get_vitest_csv_path(self.commit_hash))
        )

        # Assert content of playwright.csv
        with open(self.retro.get_playwright_csv_path(self.commit_hash)) as f:
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
                self.commit_hash,
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
                self.commit_hash,
                "playwright",
                "test2",
                "failed",
                "0.2",
                "",
            ],
        )

        # Assert content of vitest.csv
        with open(self.retro.get_vitest_csv_path(self.commit_hash)) as f:
            reader = csv.reader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 3)  # Header + 2 test cases
        self.assertEqual(
            rows[0],
            ["Commit", "Test Type", "Test Name", "Result", "Duration", "Media Path"],
        )
        self.assertEqual(
            rows[1], [self.commit_hash, "vitest", "test3", "passed", "0.3", ""]
        )
        self.assertEqual(
            rows[2], [self.commit_hash, "vitest", "test4", "failed", "0.4", ""]
        )
