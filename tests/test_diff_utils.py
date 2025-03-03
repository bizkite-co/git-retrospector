#!/usr/bin/env python3
import unittest
import os
import shutil
import tempfile
import subprocess
from git_retrospector.diff_utils import generate_diff
from git_retrospector.retro import Retro


class TestGenerateDiff(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        self.retro = Retro(
            name="test_retro", repo_under_test_path=self.repo_dir, output_paths={}
        )
        # Initialize a git repo
        subprocess.run(
            ["git", "init"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        # Create an initial commit
        with open(os.path.join(self.repo_dir, "file1.txt"), "w") as f:
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
        self.commit1 = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=self.repo_dir, text=True
        ).strip()

        # Create a second commit
        with open(os.path.join(self.repo_dir, "file1.txt"), "w") as f:
            f.write("Modified content")
        subprocess.run(
            ["git", "add", "."],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Second commit"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        self.commit2 = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=self.repo_dir, text=True
        ).strip()

    def test_generate_diff(self):
        # Create dummy directories and files for the test
        commit_hash_dir, tool_summary_dir = self.retro.create_commit_hash_dir(
            self.commit2
        )  # Use commit2 as the "current" commit

        # Call generate_diff with correct arguments
        generate_diff(
            retro=self.retro,
            repo_path=self.repo_dir,
            commit1=self.commit1,
            commit2=self.commit2,
            output_path=os.path.join(commit_hash_dir, "test.diff"),
        )

        # Assert that the diff file is created correctly
        diff_file_path = os.path.join(commit_hash_dir, "test.diff")
        self.assertTrue(os.path.exists(diff_file_path))

        # Add assertions to check the content of the diff files if needed

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
