#!/usr/bin/env python3
import unittest
import os
import shutil
import tempfile
from git_retrospector.parser import parse_commit_results
from git_retrospector.retro import Retro

# from TestConfig import BaseTest # No longer needed


class TestParseCommitResults(
    unittest.TestCase
):  # Inherit directly from unittest.TestCase
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        self.retro = Retro(
            name="test_retro", repo_under_test_path=self.repo_dir, output_paths={}
        )
        self.commit_hash = "test_commit"
        # Create the necessary directory structure
        self.commit_hash_dir, self.tool_summary_dir = self.retro.create_commit_hash_dir(
            self.commit_hash
        )

    def test_parse_commit_results(self):
        # Create dummy XML files (replace with actual test data)
        playwright_xml_path = self.retro.get_playwright_xml_path(self.commit_hash)
        vitest_log_path = self.retro.get_vitest_log_path(self.commit_hash)
        with open(playwright_xml_path, "w") as f:
            f.write("<testsuite></testsuite>")  # Minimal valid XML
        with open(vitest_log_path, "w") as f:
            f.write("<testsuites></testsuites>")  # Minimal valid XML for Vitest
        # Call parse_commit_results
        parse_commit_results(self.retro, self.commit_hash)

        # Assert that the CSV files are created
        self.assertTrue(
            os.path.exists(self.retro.get_playwright_csv_path(self.commit_hash))
        )
        self.assertTrue(
            os.path.exists(self.retro.get_vitest_csv_path(self.commit_hash))
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
