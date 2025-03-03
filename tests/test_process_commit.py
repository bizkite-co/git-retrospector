#!/usr/bin/env python3
import unittest
import os
import shutil
import tempfile
import subprocess
from git_retrospector.commit_processor import process_commit
from git_retrospector.retro import Retro

# from TestConfig import BaseTest # No longer needed


class TestProcessCommit(unittest.TestCase):  # Inherit directly from unittest.TestCase

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        self.retro = Retro(
            name="test_retro", repo_under_test_path=self.repo_dir, output_paths={}
        )
        self.commit_hash = "test_commit"
        # Initialize a git repo
        subprocess.run(
            ["git", "init"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        # Create an initial commit
        with open(os.path.join(self.repo_dir, "test_file.txt"), "w") as f:
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

    def test_process_commit(self):
        # Call process_commit (replace with actual arguments if needed)
        process_commit(
            target_repo=self.repo_dir,
            commit_hash=self.commit_hash,
            output_dir=self.temp_dir,  # Use temp_dir for output
            origin_branch="main",  # Replace with the actual origin branch
            retro=self.retro,
        )

        # Add assertions to check the expected outcome (files created, etc.)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
