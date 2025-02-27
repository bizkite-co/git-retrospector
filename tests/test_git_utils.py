import unittest
import subprocess
import tempfile
import os
from git_retrospector.git_utils import get_current_commit_hash, find_screenshot


class TestGitUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        subprocess.run(
            ["git", "init"],
            cwd=self.temp_dir.name,
            check=True,
            capture_output=True,
        )
        # Create an empty initial commit
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Initial empty commit"],
            cwd=self.temp_dir.name,
            check=True,
            capture_output=True,
        )
        self.repo_path = self.temp_dir.name
        self.commit_hash = get_current_commit_hash(self.repo_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_current_commit_hash(self):
        commit_hash = get_current_commit_hash(self.repo_path)
        self.assertIsInstance(commit_hash, str)
        self.assertTrue(len(commit_hash) > 0)

    def test_find_screenshot(self):
        # Create a dummy test directory structure
        test_name = "My Test Case"
        commit_dir = os.path.join(self.temp_dir.name, "commit_dir")
        screenshots_dir = os.path.join(commit_dir, "screenshots")
        os.makedirs(screenshots_dir)

        # Test case 1: Screenshot exists
        screenshot_name = "My_Test_Case.png"  # Expected name
        screenshot_path = os.path.join(screenshots_dir, screenshot_name)
        with open(screenshot_path, "w") as f:
            f.write("Dummy screenshot content")

        found_path = find_screenshot(test_name, commit_dir)
        self.assertEqual(found_path, os.path.abspath(screenshot_path))

        # Test case 2: Screenshot does not exist
        os.remove(screenshot_path)  # Remove the screenshot
        found_path = find_screenshot(test_name, commit_dir)
        self.assertIsNone(found_path)

        # Test case 3: Different test name with spaces and slashes
        test_name_2 = "Another/Test Name With Spaces"
        screenshot_name_2 = "Another_Test_Name_With_Spaces.png"
        screenshot_path_2 = os.path.join(screenshots_dir, screenshot_name_2)

        with open(screenshot_path_2, "w") as f:
            f.write("Dummy content for test 2")

        found_path_2 = find_screenshot(test_name_2, commit_dir)
        self.assertEqual(found_path_2, os.path.abspath(screenshot_path_2))
