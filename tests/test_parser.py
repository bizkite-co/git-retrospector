#!/usr/bin/env python3
import unittest
import os
import shutil
import tempfile
from git_retrospector.parser import _process_vitest_log, _process_playwright_xml
from git_retrospector.retro import Retro

# from TestConfig import BaseTest # No longer needed


class TestParser(unittest.TestCase):  # Inherit directly from unittest.TestCase
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

    def test_process_vitest_log(self):
        # Create a dummy vitest.log file (replace with actual test data)
        vitest_log_path = self.retro.get_vitest_log_path(self.commit_hash)
        with open(vitest_log_path, "w") as f:
            f.write("test log content")

        # Call _process_vitest_log
        _process_vitest_log(self.retro, vitest_log_path, self.commit_hash)

        # Add assertions to check the expected outcome

    def test_process_playwright_xml(self):
        # Create a dummy playwright.xml file (replace with actual test data)
        playwright_xml_path = self.retro.get_playwright_xml_path(self.commit_hash)
        with open(playwright_xml_path, "w") as f:
            f.write("<testsuite></testsuite>")  # Minimal valid XML

        # Call _process_playwright_xml
        _process_playwright_xml(self.retro, playwright_xml_path, self.commit_hash)

        # Add assertions to check the expected outcome

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
