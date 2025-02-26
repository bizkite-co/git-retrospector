import unittest
import os
import tempfile
import toml
from git_retrospector.retrospector import initialize


class TestInitialize(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initialize(self):
        target_name = "test_target"
        repo_path = os.path.join(self.temp_dir.name, "repo")
        os.makedirs(repo_path)
        config_file_path = initialize(target_name, repo_path, self.temp_dir.name)
        self.assertTrue(os.path.exists(config_file_path))

        config = toml.load(config_file_path)
        self.assertEqual(config["name"], target_name)
        self.assertEqual(config["repo_under_test_path"], repo_path)
        self.assertTrue(config["test_result_dir"].startswith(self.temp_dir.name))
