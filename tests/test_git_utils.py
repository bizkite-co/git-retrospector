import unittest
import subprocess
import tempfile
from git_retrospector.retrospector import get_current_commit_hash


class TestGitUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        subprocess.run(["git", "init"], cwd=self.temp_dir.name, check=True)
        # Create an empty initial commit
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Initial empty commit"],
            cwd=self.temp_dir.name,
            check=True,
        )
        self.repo_path = self.temp_dir.name
        self.commit_hash = get_current_commit_hash(self.repo_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_current_commit_hash(self):
        commit_hash = get_current_commit_hash(self.repo_path)
        self.assertIsInstance(commit_hash, str)
        self.assertTrue(len(commit_hash) > 0)
