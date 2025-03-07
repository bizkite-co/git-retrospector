#!/usr/bin/env python3
import unittest
import os
import shutil
import tempfile
from pathlib import Path
from git_retrospector.retro import Retro

# from TestConfig import BaseTest # No longer needed


class TestRetro(unittest.TestCase):  # Inherit directly from unittest.TestCase
    temp_dir: str

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        self.retro = Retro(
            name="test_retro_instance",
            repo_under_test_path=self.repo_dir,
            # output_paths={},  # Removed
        )
        self.retro.init_repo()  # Initialize a git repo in the temp dir
        # logging.debug(f"Created retro: {self.retro}") # Removed
        # logging.info(f"setUp CWD: {os.getcwd()}") # Removed

    def test_get_retro_dir(self):
        # This test doesn't actually test anything now, but we'll leave it
        # in place for now.  It at least exercises the constructor.
        return self.retro.get_retro_dir()

    # def test_create_retro_tree(self): # Removed

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_local_test_output_dir_full(self):
        """Test that local_test_output_dir_full is initialized correctly."""
        expected_path = os.path.join("retros", "test_retro_instance", "test-output")
        self.assertEqual(self.retro.local_test_output_dir_full, expected_path)

    def test_move_test_results_to_local(self):
        """Test that test results are moved correctly."""
        # 1. Create a dummy test-results directory in the remote_repo_path
        test_results_dir = Path(self.repo_dir) / "test-results"
        test_results_dir.mkdir()
        vitest_xml = test_results_dir / "vitest.xml"  # Changed to vitest.xml
        playwright_xml = test_results_dir / "playwright.xml"
        vitest_xml.write_text("Vitest test output")  # Changed to vitest.xml
        playwright_xml.write_text("<xml>Playwright test output</xml>")

        # 2. Call move_test_results_to_local with a test commit hash
        commit_hash = "test_commit"
        self.retro.move_test_results_to_local(commit_hash, "test-results")

        # 3. Assert that the files have been moved to the correct location
        expected_local_dir = (
            Path(self.retro.get_retro_dir()) / "test-output" / commit_hash
        )
        self.assertTrue(expected_local_dir.exists())
        self.assertTrue(
            (expected_local_dir / "vitest.xml").exists()
        )  # Changed to vitest.xml
        self.assertTrue((expected_local_dir / "playwright.xml").exists())

        # 4. Assert that the original directory is removed
        self.assertFalse(test_results_dir.exists())
