import unittest
import tempfile
import os
import shutil

from git_retrospector.git_retrospector import Retro


class TestRetroProcessor(unittest.TestCase):
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
