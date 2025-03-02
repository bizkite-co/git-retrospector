import subprocess
from TestConfig import BaseTest
from git_retrospector.git_utils import get_current_commit_hash


class TestGitUtils(BaseTest):
    def setUp(self):
        super().setUp()
        subprocess.run(
            ["git", "init"], cwd=self.temp_dir, check=True, capture_output=True
        )
        # Create an empty initial commit
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Initial empty commit"],
            cwd=self.temp_dir,
            check=True,
            capture_output=True,
        )
        self.repo_path = self.temp_dir
        self.commit_hash = get_current_commit_hash(self.repo_path)

    # def tearDown(self):
    #     self.temp_dir.cleanup()

    def test_get_current_commit_hash(self):
        commit_hash = get_current_commit_hash(self.repo_path)
        self.assertIsInstance(commit_hash, str)
        self.assertTrue(len(commit_hash) > 0)
