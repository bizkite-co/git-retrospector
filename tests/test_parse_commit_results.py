import unittest
import tempfile
import os
import shutil
from unittest.mock import patch  # Import call
from pathlib import Path  # Import Path

# Correct the import name
from git_retrospector.parser import parse_commit_results
from git_retrospector.retro import Retro


class TestParseCommitResults(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        # Simulate the structure expected by Retro paths
        self.mock_retro_base = Path(self.temp_dir)
        self.target_name = "test_retro"
        self.commit_hash = "test_commit"
        self.original_cwd = Path.cwd()  # Capture original CWD

        # Define paths
        self.mock_repo_path = self.mock_retro_base / "test_repo"
        # Output dir is relative to project root (original_cwd)
        self.mock_output_dir = (
            self.original_cwd / "retros" / self.target_name / "test-output"
        )
        self.mock_commit_dir = self.mock_output_dir / self.commit_hash
        self.mock_tool_summary_dir = self.mock_commit_dir / "tool-summary"

        # Create directories mocks might need to interact with
        os.makedirs(self.mock_repo_path, exist_ok=True)  # Create the repo dir
        self.mock_tool_summary_dir.mkdir(parents=True, exist_ok=True)

        # Initialize a Retro object for testing
        self.retro = Retro(
            name=self.target_name,
            remote_repo_path=str(self.mock_repo_path),  # Use string path of created dir
            test_output_dir="test-output",
            github_remote="",
            github_repo_name="",
            github_repo_owner="",
            github_project_name="",
            github_project_number=0,
            github_project_owner="",
            test_result_dir="",
            test_runners=[],  # Provide an empty list
        )
        # Mock Path.cwd() if Retro methods rely on it relative to project root
        self.cwd_patcher = patch("pathlib.Path.cwd", return_value=self.original_cwd)
        self.mock_cwd = self.cwd_patcher.start()

    def tearDown(self):
        # Clean up the temporary directory after each test
        shutil.rmtree(self.temp_dir)
        # Clean up retro dir created in project structure
        retro_dir_in_project = self.original_cwd / "retros" / self.target_name
        if retro_dir_in_project.exists():
            shutil.rmtree(retro_dir_in_project)
        self.cwd_patcher.stop()

    @patch("git_retrospector.parser._process_vitest_xml")
    @patch("git_retrospector.parser._process_playwright_xml")
    @patch(
        "git_retrospector.retro.Retro.path_exists", return_value=False
    )  # Mock path_exists
    def test_parse_commit_results_no_files(
        self, mock_path_exists, mock_process_playwright, mock_process_vitest
    ):
        parse_commit_results(self.retro, self.commit_hash)

        # Calculate expected relative paths as strings
        expected_rel_vitest_str = f"test-output/{self.commit_hash}/vitest.xml"
        expected_rel_playwright_str = f"test-output/{self.commit_hash}/playwright.xml"

        # Check the calls made to the mock, comparing string arguments
        calls = mock_path_exists.call_args_list
        # Extract the first argument (the path) from each call and convert to string
        called_paths = [str(c.args[0]) for c in calls]
        self.assertIn(
            expected_rel_vitest_str,
            called_paths,
            f"Call with '{expected_rel_vitest_str}' not found in {called_paths}",
        )
        self.assertIn(
            expected_rel_playwright_str,
            called_paths,
            f"Call with '{expected_rel_playwright_str}' not found in {called_paths}",
        )

        # Assert that the processing functions were NOT called
        mock_process_vitest.assert_not_called()
        mock_process_playwright.assert_not_called()

    @patch("git_retrospector.parser._process_vitest_xml")
    @patch("git_retrospector.parser._process_playwright_xml")
    @patch("git_retrospector.retro.Retro.path_exists")  # Mock path_exists dynamically
    def test_parse_commit_results_files_exist(
        self, mock_path_exists, mock_process_playwright, mock_process_vitest
    ):
        # Calculate expected relative paths as strings
        expected_rel_vitest_str = f"test-output/{self.commit_hash}/vitest.xml"
        expected_rel_playwright_str = f"test-output/{self.commit_hash}/playwright.xml"

        # Simulate that both XML files exist by having path_exists return True
        def side_effect(path_arg):
            # path_arg is the relative path string passed to path_exists
            return (
                str(path_arg) == expected_rel_vitest_str
                or str(path_arg) == expected_rel_playwright_str
            )

        mock_path_exists.side_effect = side_effect

        # Get absolute paths for asserting calls to processing functions
        vitest_abs = self.retro.get_vitest_xml_path(self.commit_hash)
        playwright_abs = self.retro.get_playwright_xml_path(self.commit_hash)

        parse_commit_results(self.retro, self.commit_hash)

        # Check the calls made to the mock, comparing string arguments
        calls = mock_path_exists.call_args_list
        called_paths = [str(c.args[0]) for c in calls]
        self.assertIn(
            expected_rel_vitest_str,
            called_paths,
            f"Call with '{expected_rel_vitest_str}' not found in {called_paths}",
        )
        self.assertIn(
            expected_rel_playwright_str,
            called_paths,
            f"Call with '{expected_rel_playwright_str}' not found in {called_paths}",
        )

        # Assert that the processing functions WERE
        # called (as path_exists returned True)
        mock_process_vitest.assert_called_once_with(
            self.retro, vitest_abs, self.commit_hash
        )
        mock_process_playwright.assert_called_once_with(
            self.retro, playwright_abs, self.commit_hash
        )
