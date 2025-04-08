#!/usr/bin/env python3
import unittest
import os
import shutil
import tempfile
import subprocess
from unittest.mock import patch, MagicMock
from git_retrospector.git_utils import (
    get_current_commit_hash,
    get_origin_branch_or_commit,
    get_commit_list,  # Import the function to test
)

# Configure logging for tests (optional, but can be helpful)
# logging.basicConfig(level=logging.DEBUG)


class TestGitUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        # Initialize a git repo using subprocess.run for better security
        subprocess.run(
            ["git", "init"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        # Need to add an initial commit, otherwise git commands will fail.
        with open(os.path.join(self.repo_dir, "test_file.txt"), "w") as f:
            f.write("Initial content")
        subprocess.run(
            ["git", "add", "."],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_get_current_commit_hash(self):
        # Test case 1: Get current commit hash in a valid Git repository.
        commit_hash = get_current_commit_hash(self.repo_dir)
        self.assertIsNotNone(commit_hash)  # Check if a commit hash is returned
        self.assertTrue(isinstance(commit_hash, str))  # Check if it's a string
        self.assertTrue(len(commit_hash) > 0)  # Check if it's not empty

        # Test case 2: Get current commit hash in a non-Git directory.
        non_git_dir = os.path.join(self.temp_dir, "non_git_dir")
        os.makedirs(non_git_dir)
        commit_hash = get_current_commit_hash(non_git_dir)
        self.assertIsNone(commit_hash)  # Should return None

    def test_get_origin_branch_or_commit(self):
        # Test case 1: Get origin branch in a valid Git repository.
        origin_branch = get_origin_branch_or_commit(self.repo_dir)
        # We may not assert the exact branch name as it can vary
        self.assertTrue(isinstance(origin_branch, str))

        # Test case 2: Get origin branch in a non-Git directory.
        non_git_dir = os.path.join(self.temp_dir, "non_git_dir")
        os.makedirs(non_git_dir)
        origin_branch = get_origin_branch_or_commit(non_git_dir)
        self.assertIsNone(origin_branch)  # Should return None

    @patch("git_retrospector.git_utils.subprocess.run")
    def test_get_commit_list_success(self, mock_run):
        # Mock successful git log command
        num_commits_to_test = 3
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = (
            "hash1|date1|summary1\n" "hash2|date2|summary2\n" "hash3|date3|summary3"
        )
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        commits = get_commit_list(self.repo_dir, num_commits=num_commits_to_test)

        # Corrected expected command based on implementation
        expected_command = [
            "git",
            "log",
            "--pretty=format:%H|%ad|%s",
            "--date=iso",
            f"-n{num_commits_to_test}",  # Combined argument
        ]
        mock_run.assert_called_once_with(
            expected_command,
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,  # Corrected: check=True is used
            encoding="utf-8",  # Corrected: encoding is specified
        )
        self.assertEqual(len(commits), 3)
        self.assertEqual(
            commits[0], {"hash": "hash1", "date": "date1", "summary": "summary1"}
        )
        self.assertEqual(
            commits[1], {"hash": "hash2", "date": "date2", "summary": "summary2"}
        )
        self.assertEqual(
            commits[2], {"hash": "hash3", "date": "date3", "summary": "summary3"}
        )

    @patch("git_retrospector.git_utils.subprocess.run")
    def test_get_commit_list_different_num_commits(self, mock_run):
        # Mock successful git log command for 2 commits
        num_commits_to_test = 2
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "hash1|date1|summary1\nhash2|date2|summary2"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        commits = get_commit_list(self.repo_dir, num_commits=num_commits_to_test)

        # Corrected expected command based on implementation
        expected_command = [
            "git",
            "log",
            "--pretty=format:%H|%ad|%s",
            "--date=iso",
            f"-n{num_commits_to_test}",  # Combined argument
        ]
        mock_run.assert_called_once_with(
            expected_command,
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,  # Corrected: check=True is used
            encoding="utf-8",  # Corrected: encoding is specified
        )
        self.assertEqual(len(commits), 2)
        self.assertEqual(
            commits[0], {"hash": "hash1", "date": "date1", "summary": "summary1"}
        )
        self.assertEqual(
            commits[1], {"hash": "hash2", "date": "date2", "summary": "summary2"}
        )

    @patch("git_retrospector.git_utils.subprocess.run")
    def test_get_commit_list_subprocess_error(self, mock_run):
        # Mock git log command failure by raising CalledProcessError
        # The function now uses check=True, so we expect CalledProcessError
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["git", "log", "..."], stderr="git error"
        )

        commits = get_commit_list(self.repo_dir, num_commits=5)

        self.assertEqual(commits, [])  # Should return an empty list on error

    @patch("git_retrospector.git_utils.subprocess.run")
    def test_get_commit_list_parsing_error(self, mock_run):
        # Mock successful git log command but with malformed output
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = (
            "hash1|date1|summary1\n"
            "malformed_line\n"  # This line should be logged as a warning
            "hash3|date3|summary3"
        )
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        # Use assertLogs to check if the warning is logged
        with self.assertLogs(level="WARNING") as log:
            commits = get_commit_list(self.repo_dir, num_commits=3)
            # Check if the expected warning message is in the logs
            self.assertTrue(
                any(
                    "Skipping malformed commit line: malformed_line" in msg
                    for msg in log.output
                )
            )

        # It should skip the malformed line and parse the valid ones
        self.assertEqual(len(commits), 2)
        self.assertEqual(
            commits[0], {"hash": "hash1", "date": "date1", "summary": "summary1"}
        )
        self.assertEqual(
            commits[1], {"hash": "hash3", "date": "date3", "summary": "summary3"}
        )

    @patch("git_retrospector.git_utils.subprocess.run")
    def test_get_commit_list_empty_output(self, mock_run):
        # Mock successful git log command with empty output (e.g., new repo)
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ""  # Empty output
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        commits = get_commit_list(self.repo_dir, num_commits=5)

        self.assertEqual(commits, [])  # Should return an empty list

    def tearDown(self):
        shutil.rmtree(self.temp_dir)


if __name__ == "__main__":
    unittest.main()
