import unittest
import tempfile
import shutil
from pathlib import Path

from git_retrospector.retro import Retro


class TestRetro(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory *outside* the project structure for isolation
        self.base_temp_dir = tempfile.mkdtemp()
        self.repo_dir = Path(self.base_temp_dir) / "test_repo"
        self.repo_dir.mkdir()

        # Store the original CWD
        self.original_cwd = Path.cwd()
        # Change CWD to a temporary base for consistent relative path testing
        # Note: This assumes tests are run from the project root initially.
        # If not, self.original_cwd might be different.
        # os.chdir(self.base_temp_dir) # Avoid changing CWD globally if possible

        # Initialize Retro object - it will use the *actual* CWD during init
        # to calculate local_cwd and local_test_output_dir_full
        self.retro = Retro(
            name="test_retro",
            remote_repo_path=str(self.repo_dir),  # Pass string path
            test_output_dir="test-output",
            test_runners=[],
        )
        # Expected path based on where the test *runs* (project root)
        self.expected_base_output_dir = (
            self.original_cwd / "retros" / "test_retro" / "test-output"
        )

    def tearDown(self):
        # Clean up the temporary directory after each test
        shutil.rmtree(self.base_temp_dir)
        # Clean up the retro directory created in the project structure
        retro_dir_in_project = self.original_cwd / "retros" / self.retro.name
        if retro_dir_in_project.exists():
            shutil.rmtree(retro_dir_in_project)
        # Restore original CWD if changed in setUp (though avoided now)
        # os.chdir(self.original_cwd)

    def test_create_and_resolve_paths(self):
        """Test that paths are created and resolved correctly."""
        # local_test_output_dir_full should be absolute path in project structure
        self.assertEqual(
            Path(self.retro.local_test_output_dir_full),  # Compare Path objects
            self.expected_base_output_dir,
            f"""Expected {
                self.expected_base_output_dir}, got {
                self.retro.local_test_output_dir_full}""",
        )
        # remote_repo_path should be the resolved absolute path of the temp repo dir
        self.assertEqual(
            self.retro.remote_repo_path,  # Already a Path object
            self.repo_dir.resolve(),  # Compare Path objects
            f"Expected {self.repo_dir.resolve()}, got {self.retro.remote_repo_path}",
        )

    def test_get_retro_dir(self):
        """Test that the retro directory is constructed correctly."""
        expected_retro_dir = self.original_cwd / "retros" / "test_retro"
        self.assertEqual(self.retro.get_retro_dir(), expected_retro_dir)

    def test_get_test_output_dir(self):
        """Test that the test output directory is constructed correctly."""
        self.assertEqual(
            self.retro.get_test_output_dir(), self.expected_base_output_dir
        )

    def test_get_test_output_dir_with_commit_hash(self):
        """Test that the test output directory with a commit hash is
        constructed correctly."""
        commit_hash = "1234567890abcdef"
        expected_test_output_dir = self.expected_base_output_dir / commit_hash
        self.assertEqual(
            self.retro.get_test_output_dir(commit_hash),
            expected_test_output_dir,
        )

    def test_get_tool_summary_dir(self):
        """Test that the tool summary directory is constructed correctly."""
        commit_hash = "1234567890abcdef"
        expected_tool_summary_dir = (
            self.expected_base_output_dir / commit_hash / "tool-summary"
        )
        self.assertEqual(
            self.retro.get_tool_summary_dir(commit_hash),
            expected_tool_summary_dir,
        )

    def test_create_and_remove_output_dirs(self):
        """Test that output directories are created and removed correctly."""
        output_dir = self.retro.get_test_output_dir()
        self.retro.create_output_dirs()
        self.assertTrue(output_dir.exists())
        self.retro.remove_output_dirs()
        self.assertFalse(output_dir.exists())

    def test_create_and_remove_output_dirs_with_commit_hash(self):
        """
        Test that output directories with a commit hash are created
        and removed correctly.
        """
        commit_hash = "1234567890abcdef"
        commit_output_dir = self.retro.get_test_output_dir(commit_hash)
        tool_summary_dir = self.retro.get_tool_summary_dir(commit_hash)

        self.retro.create_output_dirs(commit_hash)
        self.assertTrue(commit_output_dir.exists())
        self.assertTrue(tool_summary_dir.exists())

        self.retro.remove_output_dirs(commit_hash)
        self.assertFalse(commit_output_dir.exists())

    def test_path_exists(self):
        """Test that path_exists method works correctly."""
        retro_dir = self.retro.get_retro_dir()
        retro_dir.mkdir(parents=True, exist_ok=True)
        dummy_file_rel = "dummy.txt"
        (retro_dir / dummy_file_rel).write_text("dummy content")

        self.assertTrue(self.retro.path_exists(dummy_file_rel))
        self.assertFalse(self.retro.path_exists("nonexistent.txt"))

    def test_is_dir(self):
        """Test that is_dir method works correctly."""
        retro_dir = self.retro.get_retro_dir()
        retro_dir.mkdir(parents=True, exist_ok=True)
        dummy_dir_rel = "dummy_dir"
        dummy_dir_abs = retro_dir / dummy_dir_rel
        dummy_dir_abs.mkdir(exist_ok=True)  # Use exist_ok=True

        self.assertTrue(self.retro.is_dir(dummy_dir_rel))
        self.assertTrue(self.retro.is_dir(str(dummy_dir_abs)))
        self.assertFalse(self.retro.is_dir("nonexistent_dir"))
        # Create the file first to test is_dir on it
        (retro_dir / "dummy.txt").touch()
        self.assertFalse(self.retro.is_dir("dummy.txt"))

    def test_list_commit_dirs(self):
        """Test that list_commit_dirs method works correctly."""
        commit1_dir = self.retro.get_test_output_dir("commit1")
        commit2_dir = self.retro.get_test_output_dir("commit2")
        commit1_dir.mkdir(parents=True, exist_ok=True)
        commit2_dir.mkdir(parents=True, exist_ok=True)
        (self.retro.get_test_output_dir() / "a_file.txt").touch()

        commit_dirs = self.retro.list_commit_dirs()
        expected_dirs = {commit1_dir, commit2_dir}
        self.assertEqual(set(commit_dirs), expected_dirs)

    def test_get_commits_log_path(self):
        """Test that get_commits_log_path method works correctly."""
        expected_path = self.retro.get_retro_dir() / "commits.log"
        self.assertEqual(self.retro.get_commits_log_path(), expected_path)

    def test_get_config_file_path(self):
        """Test that get_config_file_path method works correctly."""
        expected_path = self.retro.get_retro_dir() / "retro.toml"
        self.assertEqual(self.retro.get_config_file_path(), expected_path)

    def test_move_test_results_to_local(self):
        """Test that test results are moved correctly."""
        source_dir_name = "test-results"
        test_results_dir = self.repo_dir / source_dir_name  # Use Path object
        test_results_dir.mkdir()
        dummy_file = test_results_dir / "dummy.txt"
        dummy_file.write_text("dummy content")

        commit_hash = "123456"
        self.retro.move_test_results_to_local(commit_hash, source_dir_name)

        local_commit_dir = self.retro.get_test_output_dir(commit_hash)
        expected_local_file = local_commit_dir / source_dir_name / "dummy.txt"
        self.assertTrue(
            expected_local_file.exists(),
            f"Expected file not found at {expected_local_file}",
        )
        self.assertFalse(
            test_results_dir.exists(),
            f"Source directory {test_results_dir} was not removed",
        )
