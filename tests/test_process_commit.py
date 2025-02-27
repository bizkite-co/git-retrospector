import unittest
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from git_retrospector.retrospector import process_commit, get_current_commit_hash


class TestProcessCommit(unittest.TestCase):
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

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("git_retrospector.commit_processor.run_vitest")
    @patch("git_retrospector.commit_processor.run_playwright")
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
        # Add a file and commit it
        with open(os.path.join(test_repo, "file1.txt"), "w") as f:
            f.write("Initial commit")
        subprocess.run(["git", "add", "."], cwd=test_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"], cwd=test_repo, check=True
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
            test_repo, str(output_dir_for_commit / "tool-summary"), mock_config
        )
        mock_run_playwright.assert_called_once_with(
            test_repo, str(output_dir_for_commit / "tool-summary"), mock_config
        )
