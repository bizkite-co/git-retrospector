#!/usr/bin/env python3
import unittest
import os
import shutil
import tempfile
import csv
from git_retrospector.retro import Retro
from git_retrospector.retrospector import process_retro

# from TestConfig import BaseTest # No longer needed


class TestRetroProcessor(unittest.TestCase):  # Inherit directly from unittest.TestCase
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        self.retro = Retro(
            name="test_retro", repo_under_test_path=self.repo_dir, output_paths={}
        )
        self.commit_hash1 = "commit1"
        self.commit_hash2 = "commit2"
        # Create necessary directories and files
        self.commit_hash_dir1, self.tool_summary_dir1 = (
            self.retro.create_commit_hash_dir(self.commit_hash1)
        )
        self.commit_hash_dir2, self.tool_summary_dir2 = (
            self.retro.create_commit_hash_dir(self.commit_hash2)
        )

    def test_process_retro(self):
        # Create dummy CSV files (replace with actual test data)
        playwright_csv_path1 = self.retro.get_playwright_csv_path(self.commit_hash1)
        vitest_csv_path1 = self.retro.get_vitest_csv_path(self.commit_hash1)
        playwright_csv_path2 = self.retro.get_playwright_csv_path(self.commit_hash2)
        vitest_csv_path2 = self.retro.get_vitest_csv_path(self.commit_hash2)

        with open(playwright_csv_path1, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Result", "Duration"])
            writer.writerow(["Test 1", "passed", "100"])

        with open(vitest_csv_path1, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Result", "Duration"])
            writer.writerow(["Test 2", "failed", "200"])

        with open(playwright_csv_path2, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Result", "Duration"])
            writer.writerow(["Test 3", "passed", "150"])

        with open(vitest_csv_path2, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Result", "Duration"])
            writer.writerow(["Test 4", "passed", "250"])

        # Call process_retro (replace with actual function call)
        process_retro(self.retro)

        # Add assertions to check the expected outcome (e.g., issues created)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
