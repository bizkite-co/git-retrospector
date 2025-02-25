import os
import subprocess
import tempfile
import unittest
from unittest.mock import mock_open, patch, MagicMock

import toml
from pathlib import Path
from git_retrospector.retrospector import (
    get_current_commit_hash,
    initialize,
    process_commit,
)
import xml.etree.ElementTree as ET
from git_retrospector.parser import (
    _process_vitest_log,
    _process_playwright_xml,
    parse_test_results,
)
from git_retrospector.xml_processor import (
    extract_media_paths,
    _write_test_case_to_csv,
    _process_test_suite,
    process_xml_string,
)


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

    @patch("git_retrospector.xml_processor.process_xml_string")
    def test_process_vitest_log(self, mock_process_xml_string):
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
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as vitest_log_file:
            vitest_log_file.write(vitest_log_content)
            vitest_log_path = vitest_log_file.name

        # Call _process_vitest_log with the mock file path
        mock_csv_writer = MagicMock()
        _process_vitest_log(vitest_log_path, "commit123", mock_csv_writer)

        # Assert that process_xml_string was called with the correct arguments
        mock_process_xml_string.assert_called_once_with(
            """<testsuites name="Vitest Tests">
          <testsuite name="Test Suite 1">
            <testcase name="Test Case 1" time="0.123" />
          </testsuite>
        </testsuites>""",
            "commit123",
            "vitest",
            mock_csv_writer,
        )

        # Clean up the temporary file
        os.remove(vitest_log_path)

    @patch("git_retrospector.xml_processor.process_xml_string")
    def test_process_playwright_xml(self, mock_process_xml_string):
        # Create a mock Playwright XML file with sample XML content
        playwright_xml_content = """
        <testsuites name="Playwright Tests">
          <testsuite name="Test Suite 1">
            <testcase name="Test Case 1" time="0.123" />
          </testsuite>
        </testsuites>
        """
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as playwright_xml_file:
            playwright_xml_file.write(playwright_xml_content)
            playwright_xml_path = playwright_xml_file.name

        # Call _process_playwright_xml with the mock file path
        mock_csv_writer = MagicMock()
        _process_playwright_xml(playwright_xml_path, "commit123", mock_csv_writer)

        # Assert that process_xml_string was called with the correct arguments
        mock_process_xml_string.assert_called_once_with(
            playwright_xml_content,
            "commit123",
            "playwright",
            mock_csv_writer,
        )

        # Clean up the temporary file
        os.remove(playwright_xml_path)

    @patch("git_retrospector.parser._process_playwright_xml")
    @patch("git_retrospector.parser._process_vitest_log")
    @patch("csv.writer")
    @patch("builtins.open", new_callable=mock_open)
    def test_parse_test_results(
        self,
        mock_open,
        mock_csv_writer,
        mock_process_vitest_log,
        mock_process_playwright_xml,
    ):

        # Configure mock_csv_writer to return a MagicMock
        mock_csv_writer.return_value = MagicMock()

        # Create mock test results directory and files
        results_dir = os.path.join(self.temp_dir.name, "results")
        commit_dir = os.path.join(results_dir, "commit123")
        os.makedirs(commit_dir)
        vitest_log_path = os.path.join(commit_dir, "vitest.log")
        playwright_xml_path = os.path.join(commit_dir, "playwright.xml")
        Path(vitest_log_path).touch()
        Path(playwright_xml_path).touch()

        # Call parse_test_results with the mock results directory
        parse_test_results(results_dir=results_dir)

        # Assert that _process_vitest_log and _process_playwright_xml were called
        mock_process_vitest_log.assert_called_once_with(
            vitest_log_path, "commit123", mock_csv_writer.return_value
        )
        mock_process_playwright_xml.assert_called_once_with(
            playwright_xml_path, "commit123", mock_csv_writer.return_value
        )

        # Assert that the output CSV file was opened in write mode
        mock_open.assert_called_once_with(
            os.path.join(os.getcwd(), "test_results_summary.csv"), "w", newline=""
        )

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

    @patch("git_retrospector.xml_processor._write_test_case_to_csv")
    def test_process_test_suite(self, mock_write_test_case_to_csv):
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
        self.assertEqual(mock_write_test_case_to_csv.call_count, 3)
        mock_write_test_case_to_csv.assert_any_call(
            mock_csv_writer, commit, test_type, "test1", "failed", 0.1, ""
        )
        mock_write_test_case_to_csv.assert_any_call(
            mock_csv_writer, commit, test_type, "test2", "passed", 0.2, ""
        )
        mock_write_test_case_to_csv.assert_any_call(
            mock_csv_writer, commit, test_type, "test3", "skipped", 0.3, ""
        )

    @patch("git_retrospector.xml_processor._process_test_suite")
    @patch("builtins.open", new_callable=mock_open)
    def test_process_xml_string(self, mock_open, mock_process_test_suite):
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

        process_xml_string(xml_string, commit, test_type, None)

        # Assert that _process_test_suite was called twice (for each testsuite)
        self.assertEqual(mock_process_test_suite.call_count, 2)


if __name__ == "__main__":
    unittest.main()
