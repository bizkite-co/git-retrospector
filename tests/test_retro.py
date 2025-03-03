#!/usr/bin/env python3
import unittest
import os
import shutil
import tempfile
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
            output_paths={},
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
