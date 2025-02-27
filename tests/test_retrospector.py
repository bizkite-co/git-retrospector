#!/usr/bin/env python3
import unittest
import os
import shutil
import toml
from pathlib import Path
from git_retrospector.config import Config


class TestConfigInitialize(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join("tests", "temp_test_config")
        self.target_name = "test_target"
        self.repo_under_test_path = os.path.join(self.test_dir, "test_repo")
        self.config_file_path = os.path.join("retros", self.target_name, "config.toml")
        os.makedirs(os.path.join(self.test_dir, "test_repo"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        if os.path.exists("retros"):
            shutil.rmtree("retros")

    def test_config_initialize(self):
        config_file_path = Config.initialize(
            self.target_name, self.repo_under_test_path, self.test_dir
        )
        self.assertTrue(os.path.exists(config_file_path))

        with open(config_file_path) as f:
            config_data = toml.load(f)

        self.assertEqual(config_data["name"], self.target_name)
        self.assertEqual(
            config_data["repo_under_test_path"],
            str(Path(self.repo_under_test_path).resolve()),
        )
        self.assertTrue(
            config_data["test_result_dir"].startswith(
                str(
                    Path(
                        os.path.join(self.test_dir, "retros", self.target_name)
                    ).resolve()
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
