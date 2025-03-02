#!/usr/bin/env python3
import logging
import os
import shutil
import tempfile
from git_retrospector.retro import Retro
from TestConfig import BaseTest


class TestRetro(BaseTest):
    temp_dir: str

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.retro = Retro(
            name="test_retro_instance",
            repo_under_test_path=self.temp_dir,
            output_paths={},
        )
        logging.debug(f"Created retro: {self.retro}")

    def test_get_retro_dir(self):
        # This test doesn't actually test anything now, but we'll leave it
        # in place for now.  It at least exercises the constructor.
        return self.retro.get_retro_dir()

    def test_create_retro_tree(self):
        retro = Retro(
            name="test_retro_tree", repo_under_test_path=self.temp_dir, output_paths={}
        )
        retro.create_commit_hash_dir("hash1")
        retro.create_commit_hash_dir("hash2")

        base_path = retro.get_test_output_dir()
        self.assertTrue(os.path.exists(base_path))
        self.assertTrue(os.path.exists(os.path.join(base_path, "hash1")))
        self.assertTrue(
            os.path.exists(os.path.join(base_path, "hash1", "tool-summary"))
        )
        self.assertTrue(os.path.exists(os.path.join(base_path, "hash2")))
        self.assertTrue(
            os.path.exists(os.path.join(base_path, "hash2", "tool-summary"))
        )
        self.assertTrue(
            os.path.exists(os.path.join("retros", "test_retro_tree", "retro.toml"))
        )

        # Optional: Log the directory structure
        logging.debug("Directory structure:")
        for dirpath, dirnames, filenames in os.walk(retro.get_retro_dir()):
            logging.debug(f"  {dirpath}")
            for dirname in dirnames:
                logging.debug(f"    {dirname}/")
            for filename in filenames:
                logging.debug(f"    {filename}")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        # No need to remove "retros/test_retro_instance" or "retros/test_retro_tree"
        # because they are created within self.temp_dir
