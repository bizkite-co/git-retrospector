import unittest
import tempfile
import os
import shutil

from git_retrospector.parser import process_commit_results
from git_retrospector.retro import Retro


class TestParseCommitResults(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)

        # Initialize a Retro object for testing
        self.retro = Retro(
            name="test_retro", remote_repo_path=self.repo_dir, test_output_dir="."
        )

    def tearDown(self):
        # Clean up the temporary directory after each test
        shutil.rmtree(self.temp_dir)

    def test_process_commit_results_no_files(self):
        result = process_commit_results(self.retro, "test_commit")
        self.assertEqual(result, [])

    def test_process_commit_results_no_matching_files(self):
        # Create a dummy file that doesn't match the expected patterns
        with open(os.path.join(self.repo_dir, "dummy.txt"), "w") as f:
            f.write("dummy content")

        result = process_commit_results(self.retro, "test_commit")
        self.assertEqual(result, [])

    # Add more test cases to cover different scenarios, such as:
    # - Files with different extensions
    # - Files in subdirectories
    # - Files with special characters in their names
    # - Empty files
    # - Very large files
