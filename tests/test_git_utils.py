#!/usr/bin/env python3
import unittest
import os
import shutil
import tempfile
import subprocess
from git_retrospector.git_utils import (
    get_current_commit_hash,
    get_origin_branch_or_commit,
)

# from TestConfig import BaseTest # No longer needed


class TestGitUtils(unittest.TestCase):  # Inherit directly from unittest.TestCase
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        # Initialize a git repo using subprocess.run for better security
        subprocess.run(
            ["git", "init"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        # Need to add an initial commit, otherwise git commands will fail.
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

    def test_get_current_commit_hash(self):
        # Test case 1: Get current commit hash in a valid Git repository.
        commit_hash = get_current_commit_hash(self.repo_dir)
        self.assertIsNotNone(commit_hash)  # Check if a commit hash is returned
        self.assertTrue(isinstance(commit_hash, str))  # Check if it's a string
        self.assertTrue(len(commit_hash) > 0)  # Check if it's not empty

        # Test case 2: Get current commit hash in a non-Git directory.
        non_git_dir = os.path.join(self.temp_dir, "non_git_dir")
        os.makedirs(non_git_dir)
        commit_hash = get_current_commit_hash(non_git_dir)
        self.assertIsNone(commit_hash)  # Should return None

    def test_get_origin_branch_or_commit(self):
        # Test case 1: Get origin branch in a valid Git repository.
        origin_branch = get_origin_branch_or_commit(self.repo_dir)
        # We may not assert the exact branch name as it can vary
        self.assertTrue(isinstance(origin_branch, str))

        # Test case 2: Get origin branch in a non-Git directory.
        non_git_dir = os.path.join(self.temp_dir, "non_git_dir")
        os.makedirs(non_git_dir)
        origin_branch = get_origin_branch_or_commit(non_git_dir)
        self.assertIsNone(origin_branch)  # Should return None

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
