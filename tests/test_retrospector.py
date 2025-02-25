import csv
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import (  # Keep these for patching in test_process_commit
    MagicMock,
    patch,
)

import toml

from git_retrospector.retrospector import (
    get_current_commit_hash,
    initialize,
    process_commit,
)

# Removed: import xml.etree.ElementTree as ET


class TestRetrospector(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        subprocess.run(["git", "init"], cwd=self.temp_dir.name, check=True)
        # Create an empty initial commit
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Initial empty commit"],
            cwd=self.temp_dir.name,
            check=True,
        )
        self.repo_path = self.temp_dir.name
        self.commit_hash = get_current_commit_hash(self.repo_path)

    def test_get_current_commit_hash(self):
        commit_hash = get_current_commit_hash(self.repo_path)
        self.assertIsInstance(commit_hash, str)
        self.assertTrue(len(commit_hash) > 0)

    def test_initialize(self):
        target_name = "test_target"
        repo_path = os.path.join(self.temp_dir.name, "repo")
        os.makedirs(repo_path)
        config_file_path = initialize(target_name, repo_path, self.temp_dir.name)
        self.assertTrue(os.path.exists(config_file_path))

        config = toml.load(config_file_path)
        self.assertEqual(config["name"], target_name)
        self.assertEqual(config["repo_under_test_path"], repo_path)
        self.assertTrue(config["test_result_dir"].startswith(self.temp_dir.name))

    @patch("git_retrospector.retrospector.run_vitest")
    @patch("git_retrospector.retrospector.run_playwright")
    def test_process_commit(self, mock_run_playwright, mock_run_vitest):
        output_dir = self.temp_dir.name
        origin_branch = "main"

        # Create a mock config object
        mock_config = MagicMock()
        mock_config.test_result_dir = Path(output_dir)

        # Create a test repo
        test_repo = os.path.join(self.temp_dir.name, "test_repo")
        os.makedirs(test_repo)
        subprocess.run(["git", "init"], cwd=test_repo, check=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Initial empty commit"],
            cwd=test_repo,
            check=True,
        )
        # Checkout the initial commit *within* the test repo
        subprocess.run(
            ["git", "checkout", "--force", self.commit_hash],
            cwd=test_repo,
            check=True,
            capture_output=True,
            text=True,
        )

        process_commit(
            test_repo, self.commit_hash, output_dir, origin_branch, mock_config
        )

        # Assert that the output directory for the commit was created
        output_dir_for_commit = Path(output_dir) / "test-output" / self.commit_hash
        self.assertTrue(output_dir_for_commit.exists())

        # Assert that run_vitest and run_playwright were called
        # with the correct arguments
        mock_run_vitest.assert_called_once_with(
            test_repo, str(output_dir_for_commit), mock_config
        )
        mock_run_playwright.assert_called_once_with(
            test_repo, str(output_dir_for_commit), mock_config
        )

    def test_parse_commit_results(self):
        # Create a temporary directory structure
        commit_dir_path = os.path.join(self.temp_dir.name, "commit_test")
        os.makedirs(commit_dir_path)

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
        with open(os.path.join(commit_dir_path, "playwright.xml"), "w") as f:
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
        with open(os.path.join(commit_dir_path, "vitest.log"), "w") as f:
            f.write(vitest_log_content)

        # Call parse_commit_results
        from git_retrospector.parser import parse_commit_results

        parse_commit_results(commit_dir_path)

        # Assert that playwright.csv and vitest.csv files were created
        self.assertTrue(os.path.exists(os.path.join(commit_dir_path, "playwright.csv")))
        self.assertTrue(os.path.exists(os.path.join(commit_dir_path, "vitest.csv")))

        # Assert content of playwright.csv
        with open(os.path.join(commit_dir_path, "playwright.csv")) as f:
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
        with open(os.path.join(commit_dir_path, "vitest.csv")) as f:
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


class TestRetroProcessor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.retro_dir = os.path.join(
            self.temp_dir.name, "retros", "test_retro", "test-output"
        )
        os.makedirs(self.retro_dir)
        self.commit_dir1 = os.path.join(self.retro_dir, "commit1")
        self.commit_dir2 = os.path.join(self.retro_dir, "commit2")
        os.makedirs(self.commit_dir1)
        os.makedirs(self.commit_dir2)

        # Create dummy playwright.xml and vitest.log files in each commit directory
        for commit_dir in [self.commit_dir1, self.commit_dir2]:
            with open(os.path.join(commit_dir, "playwright.xml"), "w") as f:
                f.write(
                    """
                    <testsuites>
                        <testsuite><testcase name='test1' time='0.1'/></testsuite>
                    </testsuites>
                    """
                )
            with open(os.path.join(commit_dir, "vitest.log"), "w") as f:
                f.write(
                    """
                    <testsuites>
                        <testsuite><testcase name='test2' time='0.2'/></testsuite>
                    </testsuites>
                    """
                )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_process_retro(self):
        # Call process_retro with the correct path
        from git_retrospector.parser import process_retro

        process_retro(os.path.join(self.temp_dir.name, "retros", "test_retro"))

        # Assert that playwright.csv and vitest.csv files were created
        # in each commit directory
        for commit_dir in [self.commit_dir1, self.commit_dir2]:
            self.assertTrue(os.path.exists(os.path.join(commit_dir, "playwright.csv")))
            self.assertTrue(os.path.exists(os.path.join(commit_dir, "vitest.csv")))


if __name__ == "__main__":
    unittest.main()
