import unittest
import tempfile
import os
import shutil
from pathlib import Path

from git_retrospector.retro import Retro


class TestRetro(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)

        # Initialize a Retro object for testing
        self.retro = Retro(
            name="test_retro",
            remote_repo_path=self.repo_dir,
            test_output_dir="test-output",  # Use a relative path
        )

    def tearDown(self):
        # Clean up the temporary directory after each test
        shutil.rmtree(self.temp_dir)

    def test_create_and_resolve_paths(self):
        """Test that paths are created and resolved correctly."""
        self.assertEqual(
            self.retro.local_test_output_dir_full,
            os.path.join(self.retro.local_cwd, "retros", "test_retro", "test-output"),
        )
        self.assertEqual(
            str(self.retro.remote_repo_path), str(Path(self.repo_dir).resolve())
        )

    def test_get_retro_dir(self):
        """Test that the retro directory is constructed correctly."""
        expected_retro_dir = os.path.join("retros", "test_retro")
        self.assertEqual(self.retro.get_retro_dir(), expected_retro_dir)

    def test_get_test_output_dir(self):
        """Test that the test output directory is constructed correctly."""
        expected_test_output_dir = os.path.join(
            self.retro.local_cwd, "retros", "test_retro", "test-output"
        )
        self.assertEqual(
            str(self.retro.get_test_output_dir()), expected_test_output_dir
        )

    def test_get_test_output_dir_with_commit_hash(self):
        """Test that the test output directory with a commit hash is
        constructed correctly."""
        commit_hash = "1234567890abcdef"
        expected_test_output_dir = os.path.join(
            self.retro.local_cwd, "retros", "test_retro", "test-output", commit_hash
        )
        self.assertEqual(
            str(self.retro.get_test_output_dir(commit_hash)),
            expected_test_output_dir,
        )

    def test_get_tool_summary_dir(self):
        """Test that the tool summary directory is constructed correctly."""
        commit_hash = "1234567890abcdef"
        expected_tool_summary_dir = os.path.join(
            self.retro.local_cwd,
            "retros",
            "test_retro",
            "test-output",
            commit_hash,
            "tool-summary",
        )
        self.assertEqual(
            str(self.retro.get_tool_summary_dir(commit_hash)),
            expected_tool_summary_dir,
        )

    def test_create_and_remove_output_dirs(self):
        """Test that output directories are created and removed correctly."""
        # Create the directories
        self.retro.create_output_dirs()
        self.assertTrue(os.path.exists(self.retro.get_test_output_dir()))

        # Remove the directories
        self.retro.remove_output_dirs()
        self.assertFalse(os.path.exists(self.retro.get_test_output_dir()))

    def test_create_and_remove_output_dirs_with_commit_hash(self):
        """
        Test that output directories with a commit hash are created
        and removed correctly.
        """
        commit_hash = "1234567890abcdef"
        # Create the directories
        self.retro.create_output_dirs(commit_hash)
        self.assertTrue(os.path.exists(self.retro.get_test_output_dir(commit_hash)))
        self.assertTrue(os.path.exists(self.retro.get_tool_summary_dir(commit_hash)))

        # Remove the directories
        self.retro.remove_output_dirs(commit_hash)
        self.assertFalse(os.path.exists(self.retro.get_test_output_dir(commit_hash)))
        self.assertFalse(os.path.exists(self.retro.get_tool_summary_dir(commit_hash)))

    def test_path_exists(self):
        """Test that path_exists method works correctly."""
        # Create a dummy file
        dummy_file_path = os.path.join(self.temp_dir, "dummy.txt")
        with open(dummy_file_path, "w") as f:
            f.write("dummy content")

        self.assertTrue(self.retro.path_exists(dummy_file_path))
        self.assertFalse(
            self.retro.path_exists(os.path.join(self.temp_dir, "nonexistent.txt"))
        )

    def test_is_dir(self):
        """Test that is_dir method works correctly."""
        # Create a dummy directory
        dummy_dir_path = os.path.join(self.temp_dir, "dummy_dir")
        os.makedirs(dummy_dir_path)

        self.assertTrue(self.retro.is_dir(dummy_dir_path))
        self.assertFalse(
            self.retro.is_dir(os.path.join(self.temp_dir, "nonexistent_dir"))
        )

    def test_list_commit_dirs(self):
        """Test that list_commit_dirs method works correctly."""
        # Create some dummy commit directories
        commit1_dir = self.retro.get_test_output_dir("commit1")
        commit2_dir = self.retro.get_test_output_dir("commit2")
        os.makedirs(commit1_dir)
        os.makedirs(commit2_dir)

        commit_dirs = self.retro.list_commit_dirs()
        self.assertEqual(len(commit_dirs), 2)
        self.assertIn(Path(commit1_dir), commit_dirs)
        self.assertIn(Path(commit2_dir), commit_dirs)

    def test_get_commits_log_path(self):
        """Test that get_commits_log_path method works correctly."""
        expected_path = Path(self.retro.get_retro_dir()) / "commits.log"
        self.assertEqual(self.retro.get_commits_log_path(), expected_path)

    def test_get_config_file_path(self):
        """Test that get_config_file_path method works correctly."""
        expected_path = Path(self.retro.get_retro_dir()) / "retro.toml"
        self.assertEqual(self.retro.get_config_file_path(), expected_path)

    def test_move_test_results_to_local(self):
        """Test that test results are moved correctly."""
        # 1. Create a dummy test-results directory in the test_retro
        test_results_dir = Path(self.repo_dir) / "test-results"
        test_results_dir.mkdir()
        # 2. Create a dummy file in test-results
        dummy_file = test_results_dir / "dummy.txt"
        dummy_file.write_text("dummy content")

        # 3. Call move_test_results_to_local with a commit hash
        commit_hash = "123456"
        self.retro.move_test_results_to_local(commit_hash, "test-results")

        # 4. Check if the file exists in the correct local directory
        local_test_output_dir = (
            Path(self.retro.get_retro_dir()) / "test-output" / commit_hash
        )
        self.assertTrue(os.path.exists(local_test_output_dir / "dummy.txt"))

        # 5. Check if the test-results directory in the remote repo is removed
        self.assertFalse(test_results_dir.exists())
