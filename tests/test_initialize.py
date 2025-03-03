#!/usr/bin/env python3
import unittest
import os
import shutil
import tempfile
import subprocess
from pathlib import Path

# from git_retrospector.retrospector import init # No longer needed
# from click.testing import CliRunner  # Import CliRunner # No longer needed
# from git_retrospector.retrospector import cli  # No longer needed
import logging
from git_retrospector.retro import Retro


class TestInitialize(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Remove the retros/test_target directory before running tests
        target_name = "test_target"
        retro_dir = Path(os.getcwd()) / "retros" / target_name
        if retro_dir.exists():
            shutil.rmtree(retro_dir)
            # print(f"Removed existing retro directory: {retro_dir}")
        target_name = "test_target_invalid"
        retro_dir = Path(os.getcwd()) / "retros" / target_name
        if retro_dir.exists():
            shutil.rmtree(retro_dir)
            # print(f"Removed existing retro directory: {retro_dir}")

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        # Initialize a git repo
        subprocess.run(
            ["git", "init"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        # Get project root (assuming test is run from project root)
        self.project_root = os.getcwd()
        logging.info(f"setUp: temp_dir = {self.temp_dir}")
        logging.info(f"setUp: repo_dir = {self.repo_dir}")
        logging.info(f"setUp: project_root = {self.project_root}")

    def test_config_initialize(self):
        # Test with correct arguments.
        target_name = "test_target"
        target_repo_path = self.repo_dir
        Retro.initialize(
            target_name, target_repo_path, self.project_root
        )  # Call directly
        config_file_path = (
            Path(self.project_root) / "retros" / target_name / "retro.toml"
        )
        self.assertTrue(config_file_path.exists())

    def test_config_initialize_invalid_repo_path(self):
        # Test with an invalid repository path.
        with self.assertRaises(ValueError):
            Retro.initialize("test_target_invalid", "invalid/path", self.project_root)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @classmethod
    def tearDownClass(cls):
        # Remove the retros/test_target directory after running all tests
        target_names = ["test_target", "test_target_invalid"]
        for target_name in target_names:
            retro_dir = Path(os.getcwd()) / "retros" / target_name
            if retro_dir.exists():
                shutil.rmtree(retro_dir)
                # print(f"Removed retro directory after tests: {retro_dir}")
