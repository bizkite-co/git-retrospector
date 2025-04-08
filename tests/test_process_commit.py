import unittest
import tempfile
import os
import shutil
from unittest.mock import patch, call, MagicMock  # Import MagicMock
import subprocess  # Import subprocess for CalledProcessError

from git_retrospector.commit_processor import process_commit
from git_retrospector.retro import Retro


class TestProcessCommit(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        # Initialize a git repo so checkout commands don't fail immediately
        subprocess.run(
            ["git", "init"], cwd=self.repo_dir, check=True, capture_output=True
        )
        with open(os.path.join(self.repo_dir, "initial.txt"), "w") as f:
            f.write("initial")
        subprocess.run(
            ["git", "add", "."], cwd=self.repo_dir, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
        )
        self.initial_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.repo_dir, text=True
        ).strip()

        # Initialize a Retro object for testing
        # Ensure test_runners is provided if the tested function uses it
        self.retro = Retro(
            name="test_retro",
            remote_repo_path=self.repo_dir,
            test_output_dir=self.temp_dir,  # Use temp_dir for simplicity here
            test_runners=[],  # Provide empty list
        )
        self.origin_branch = "main"  # Assume main for testing

    def tearDown(self):
        # Clean up the temporary directory after each test
        shutil.rmtree(self.temp_dir)

    @patch("git_retrospector.commit_processor.subprocess.run")
    @patch("git_retrospector.retro.Retro.create_output_dirs")  # Mock dir creation
    @patch("git_retrospector.retro.Retro.run_tests")  # Mock test running
    @patch(
        "git_retrospector.retro.Retro.move_test_results_to_local"
    )  # Mock moving results
    def test_process_commit_checkout_success(
        self, mock_move, mock_run_tests, mock_create_dirs, mock_subprocess_run
    ):
        # Mock the subprocess.run calls:
        # 1. Successful checkout of commit_hash
        # 2. Successful checkout back to origin_branch
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0),  # First call (checkout commit_hash)
            MagicMock(returncode=0),  # Second call (checkout origin_branch)
        ]
        commit_hash_to_test = "test_commit_hash"  # Use a distinct hash

        process_commit(
            self.repo_dir,
            commit_hash_to_test,
            self.temp_dir,
            self.origin_branch,
            self.retro,
        )

        # Assert that the *first* git checkout call was for the specific commit
        expected_checkout_call = call(
            ["git", "checkout", commit_hash_to_test],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        # Assert that the *second* call was to switch back
        expected_switch_back_call = call(
            ["git", "checkout", "--force", self.origin_branch],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )

        # Check if the expected calls are present in the call list
        self.assertIn(expected_checkout_call, mock_subprocess_run.call_args_list)
        self.assertIn(expected_switch_back_call, mock_subprocess_run.call_args_list)
        # Optionally check the order if necessary
        self.assertEqual(mock_subprocess_run.call_args_list[0], expected_checkout_call)
        self.assertEqual(
            mock_subprocess_run.call_args_list[1], expected_switch_back_call
        )

        # Assert other mocks were called
        mock_create_dirs.assert_called_once_with(commit_hash_to_test)

    @patch("git_retrospector.commit_processor.subprocess.run")
    @patch("git_retrospector.retro.Retro.create_output_dirs")  # Mock dir creation
    @patch("git_retrospector.retro.Retro.run_tests")  # Mock test running
    @patch(
        "git_retrospector.retro.Retro.move_test_results_to_local"
    )  # Mock moving results
    def test_process_commit_checkout_failure(
        self, mock_move, mock_run_tests, mock_create_dirs, mock_subprocess_run
    ):
        # Mock the subprocess.run call for git checkout to simulate failure
        # The first call raises CalledProcessError
        # The second call (in finally) should still happen and succeed
        checkout_error = subprocess.CalledProcessError(
            1, ["git", "checkout", "..."], stderr="Checkout failed"
        )
        mock_subprocess_run.side_effect = [
            checkout_error,
            MagicMock(returncode=0),  # Second call (checkout origin_branch) succeeds
        ]
        commit_hash_to_test = "test_commit_hash"

        # Run the function (it should catch the CalledProcessError)
        process_commit(
            self.repo_dir,
            commit_hash_to_test,
            self.temp_dir,
            self.origin_branch,
            self.retro,
        )

        # Assert that the first git checkout call was attempted
        expected_checkout_call = call(
            ["git", "checkout", commit_hash_to_test],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        # Assert that the second call (switch back) was still made in finally block
        expected_switch_back_call = call(
            ["git", "checkout", "--force", self.origin_branch],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )

        # Check the calls were made
        self.assertIn(expected_checkout_call, mock_subprocess_run.call_args_list)
        self.assertIn(expected_switch_back_call, mock_subprocess_run.call_args_list)
        # Check the order
        self.assertEqual(mock_subprocess_run.call_args_list[0], expected_checkout_call)
        self.assertEqual(
            mock_subprocess_run.call_args_list[1], expected_switch_back_call
        )

        # Assert that directory creation and test running were NOT
        # called due to early exit
        mock_create_dirs.assert_not_called()
        mock_run_tests.assert_not_called()
        mock_move.assert_not_called()
