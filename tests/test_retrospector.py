#!/usr/bin/env python3
import unittest
from pathlib import Path

from git_retrospector.retro import Retro
from git_retrospector.parser import _process_playwright_xml
from TestConfig import BaseTest


class TestConfigInitialize(BaseTest):

    def test_config_initialize(self):
        # The test_repo directory is now created in BaseTest.setUpClass

        # Get the expected repo path
        repo_under_test_path = Path(self.temp_dir) / "test_repo"

        # Instead of checking the config file, which might have been created
        # with a different path, let's check the retro object's attributes directly
        self.assertEqual(
            str(self.retro.repo_under_test_path), str(repo_under_test_path.resolve())
        )

        # Check that the test_output_dir_full is set correctly
        self.assertEqual(
            self.retro.test_output_dir_full,
            str(repo_under_test_path / self.retro.test_output_dir),
        )

        # Check that the output_paths is empty (as set in BaseTest)
        self.assertEqual(self.retro.output_paths, {})

    def test_config_initialize_invalid_repo_path(self):
        """Test initialization with an invalid repository path."""
        with self.assertRaises(ValueError):
            Retro(
                name="test_target", repo_under_test_path="invalid/path", output_paths={}
            )


class TestCSVOutput(BaseTest):
    def setUp(self):
        super().setUp()
        self.commit_hash = "test_commit"
        # Create the necessary directory structure
        self.retro.create_commit_hash_dir(self.commit_hash)

        # Create a sample XML file *next* to tool-summary
        self.xml_content = """
        <testsuites name="Playwright Tests">
          <testsuite name="Suite1">
            <testcase name="test_example" time="0.1">
              <failure>Error message</failure>
            </testcase>
          </testsuite>
        </testsuites>
        """
        self.xml_file_path = self.retro.get_playwright_xml_path(self.commit_hash)
        with open(self.xml_file_path, "w") as f:
            f.write(self.xml_content)

    def test_csv_output_creation(self):
        # Create the CSV file directly instead of relying on run_tests
        # This simulates what run_tests would do
        _process_playwright_xml(self.retro, self.xml_file_path, self.commit_hash)

        # Check if the CSV file was created in the correct location
        expected_csv_path = self.retro.get_playwright_csv_path(self.commit_hash)
        self.assertTrue(
            expected_csv_path.exists(), f"CSV file not found at {expected_csv_path}"
        )

        # Optionally, check the content of the CSV file
        with open(expected_csv_path) as f:
            content = f.read()
            self.assertIn("test_example", content)
            self.assertIn("failed", content)

    def test_csv_output_creation_missing_xml(self):
        # Do *not* create the XML file
        # Call run with commit and retro file

        # Remove the XML file, so it will be missing
        self.xml_file_path.unlink()

        # Also remove any existing CSV file to ensure a clean test
        csv_path = self.retro.get_playwright_csv_path(self.commit_hash)
        if csv_path.exists():
            csv_path.unlink()

        # Instead of calling run_tests, which would try to process all commits,
        # we'll directly call the parser function that would be called by run_tests

        # The function should handle the missing XML file gracefully
        # and not create a CSV file
        _process_playwright_xml(self.retro, self.xml_file_path, self.commit_hash)

        # Check that the CSV file was *not* created
        expected_csv_path = self.retro.get_playwright_csv_path(self.commit_hash)
        self.assertFalse(
            expected_csv_path.exists(),
            f"CSV file should not exist: {expected_csv_path}",
        )


if __name__ == "__main__":
    unittest.main()
