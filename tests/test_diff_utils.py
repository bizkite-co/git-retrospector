import unittest
import tempfile
import os
import shutil

from git_retrospector.diff_utils import (
    filter_diff_by_filenames,
)
from git_retrospector.retro import Retro


class TestDiffUtils(unittest.TestCase):
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

    def test_filter_diff_by_filenames(self):
        diff_content = """diff --git a/file1.txt b/file1.txt
    --- a/file1.txt
    +++ b/file1.txt
    @@ -1,1 +1,1 @@
    -old content
    +new content
    diff --git a/file2.txt b/file2.txt
    --- a/file2.txt
    +++ b/file2.txt
    @@ -1,1 +1,1 @@
    -old content
    +new content
    """
        filenames = ["file1.txt"]
        filtered_diff = filter_diff_by_filenames(diff_content, filenames)
        expected_diff = """diff --git a/file1.txt b/file1.txt
    --- a/file1.txt
    +++ b/file1.txt
    @@ -1,1 +1,1 @@
    -old content
    +new content
    """
        self.assertEqual(filtered_diff, expected_diff)

    def test_filter_diff_by_filenames_no_match(self):
        diff_content = """diff --git a/file1.txt b/file1.txt
    --- a/file1.txt
    +++ b/file1.txt
    @@ -1,1 +1,1 @@
    -old content
    +new content
    """
        filenames = ["file2.txt"]
        filtered_diff = filter_diff_by_filenames(diff_content, filenames)
        self.assertEqual(filtered_diff, "")
