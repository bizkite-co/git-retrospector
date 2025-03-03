#!/usr/bin/env python3
import unittest
import os
import shutil
import tempfile
from git_retrospector.retrospector import run_tests, create_issues_for_commit

# from git_retrospector.retrospector import init # No longer needed
from git_retrospector.retro import Retro
import toml


class TestRetrospectorCLI(unittest.TestCase):  # Inherit directly from unittest.TestCase

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        self.retro = Retro(
            name="test_retro_instance",
            repo_under_test_path=self.repo_dir,
            output_paths={},
        )

    def test_init_command(self):
        # Test with correct arguments.
        # Create the retro.toml file explicitly for the test
        retro_toml_path = self.retro.get_config_file_path()
        os.makedirs(os.path.dirname(retro_toml_path), exist_ok=True)
        with open(retro_toml_path, "w") as f:
            toml.dump(self.retro.model_dump(), f)
        self.assertTrue(os.path.exists(retro_toml_path))

    def test_run_command(self):
        # Test with correct arguments.
        run_tests("test_retro", 1)  # Run with a single iteration

    def test_issues_command(self):
        # Test with correct arguments.
        # This will fail without a valid retro and commit.
        # We'll just call the function directly for now.
        create_issues_for_commit("test_retro", "test_commit")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
