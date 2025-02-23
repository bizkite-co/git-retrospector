import unittest
import tempfile
import subprocess
import os
from git_test_retrospector.retrospector import get_current_commit_hash

class TestRetrospector(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        subprocess.run(['git', 'init'], cwd=self.temp_dir.name, check=True)
        # Create an empty initial commit
        subprocess.run(['git', 'commit', '--allow-empty', '-m', 'Initial empty commit'], cwd=self.temp_dir.name, check=True)
        self.repo_path = self.temp_dir.name

    def test_get_current_commit_hash(self):
        result = get_current_commit_hash(self.repo_path)
        self.assertTrue(isinstance(result, str))
        self.assertIsNotNone(result)

    def tearDown(self):
        self.temp_dir.cleanup()

if __name__ == '__main__':
    unittest.main()