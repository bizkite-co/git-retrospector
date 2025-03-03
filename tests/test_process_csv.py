#!/usr/bin/env python3
import unittest
import os
import shutil
import tempfile
import csv
from git_retrospector.retrospector import process_csv_files
from git_retrospector.retro import Retro

# from TestConfig import BaseTest # No longer needed


class TestProcessCSV(unittest.TestCase):  # Inherit directly from unittest.TestCase
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Create a test_repo directory in the temp_dir
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        self.retro = Retro(
            name="test_retro", repo_under_test_path=self.repo_dir, output_paths={}
        )

    def test_process_csv_files(self):
        # Create dummy CSV files (replace with actual test data)
        playwright_csv_path = os.path.join(self.temp_dir, "playwright.csv")
        vitest_csv_path = os.path.join(self.temp_dir, "vitest.csv")

        with open(playwright_csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Result", "Duration"])
            writer.writerow(["Test 1", "passed", "100"])
            writer.writerow(["Test 2", "failed", "200"])

        with open(vitest_csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Result", "Duration"])
            writer.writerow(["Test 3", "passed", "150"])
            writer.writerow(["Test 4", "failed", "250"])

        # Call process_csv_files (replace with actual function call and arguments)
        # Create a mock repo object for testing
        class MockRepo:
            def create_issue(self, title, body):
                # print(f"Creating issue with title: {title}")
                # print(f"Body:\n{body}")
                pass

        mock_repo = MockRepo()

        process_csv_files(mock_repo, playwright_csv_path, vitest_csv_path)

        # Add assertions to check the expected outcome (e.g., issues created)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
