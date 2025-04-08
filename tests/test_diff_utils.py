import unittest
import tempfile
import os
import shutil
from pathlib import Path  # Import Path

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
            test_runners=[],  # Add default
        )

    def tearDown(self):
        # Clean up the temporary directory after each test
        shutil.rmtree(self.temp_dir)
        # Clean up retro dir created in project structure
        retro_dir_in_project = Path.cwd() / "retros" / self.retro.name
        if retro_dir_in_project.exists():
            shutil.rmtree(retro_dir_in_project)

    def test_filter_diff_by_filenames(self):
        # Use raw string or escape sequences if diff has special chars
        diff_content = (
            "diff --git a/file1.txt b/file1.txt\n"
            "--- a/file1.txt\n"
            "+++ b/file1.txt\n"
            "@@ -1,1 +1,1 @@\n"
            "-old content\n"
            "+new content\n"
            "diff --git a/file2.txt b/file2.txt\n"
            "--- a/file2.txt\n"
            "+++ b/file2.txt\n"
            "@@ -1,1 +1,1 @@\n"
            "-old content\n"
            "+new content\n"
        )
        filenames = ["file1.txt"]
        filtered_diff = filter_diff_by_filenames(diff_content, filenames)
        # Define expected string explicitly with correct newlines
        expected_diff = (
            "diff --git a/file1.txt b/file1.txt\n"
            "--- a/file1.txt\n"
            "+++ b/file1.txt\n"
            "@@ -1,1 +1,1 @@\n"
            "-old content\n"
            "+new content\n"  # Ensure single trailing newline matches function output
        )
        # Use assertMultiLineEqual for better diff output on failure
        self.assertMultiLineEqual(filtered_diff, expected_diff)

    def test_filter_diff_by_filenames_no_match(self):
        diff_content = (
            "diff --git a/file1.txt b/file1.txt\n"
            "--- a/file1.txt\n"
            "+++ b/file1.txt\n"
            "@@ -1,1 +1,1 @@\n"
            "-old content\n"
            "+new content\n"
        )
        filenames = ["file2.txt"]
        filtered_diff = filter_diff_by_filenames(diff_content, filenames)
        self.assertEqual(filtered_diff, "")
