import unittest
import tempfile
import os
import shutil
from unittest.mock import patch

from git_retrospector.commit_processor import process_commit
from git_retrospector.retro import Retro


class TestProcessCommit(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)

        # Initialize a Retro object for testing
        self.retro = Retro(
            name="test_retro",
            remote_repo_path=self.repo_dir,
            test_output_dir=self.temp_dir,
        )

    def tearDown(self):
        # Clean up the temporary directory after each test
        shutil.rmtree(self.temp_dir)

    @patch("subprocess.run")
    def test_process_commit_checkout_success(self, mock_run):
        # Mock the subprocess.run call for git checkout
        mock_run.return_value.returncode = 0

        process_commit(
            self.repo_dir, "test_commit_hash", "test_output_dir", "main", self.retro
        )

        # Assert that git checkout was called with the correct arguments
        mock_run.assert_called_with(
            ["git", "checkout", "test_commit_hash"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )

    @patch("subprocess.run")
    def test_process_commit_checkout_failure(self, mock_run):
        # Mock the subprocess.run call for git checkout to simulate failure
        mock_run.return_value.returncode = 1

        process_commit(
            self.repo_dir, "test_commit_hash", "test_output_dir", "main", self.retro
        )

        # Assert that git checkout was called with the correct arguments
        mock_run.assert_called_with(
            ["git", "checkout", "test_commit_hash"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        # Add more assertions as needed, e.g., check for logging, etc.
