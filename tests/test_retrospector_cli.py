#!/usr/bin/env python3
import unittest
import os
from git_retrospector.retrospector import run_tests, create_issues_for_commit
from TestConfig import BaseTest


class TestRetrospectorCLI(BaseTest):
    def test_init_command(self):
        # Test with correct arguments.
        self.assertTrue(os.path.exists(self.retro.get_config_file_path()))

    def test_run_command(self):
        # Test with correct arguments.
        run_tests("test_retro", 1)  # Run with a single iteration

    def test_issues_command(self):
        # Test with correct arguments.
        # This will fail without a valid retro and commit.
        # We'll just call the function directly for now.
        create_issues_for_commit("test_retro", "test_commit")


if __name__ == "__main__":
    unittest.main()
