import unittest
import os
import tempfile

from git_retrospector.parser import process_retro


class TestRetroProcessor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.retro_dir = os.path.join(
            self.temp_dir.name, "retros", "test_retro", "test-output"
        )
        os.makedirs(self.retro_dir)
        self.commit_dir1 = os.path.join(self.retro_dir, "commit1")
        self.commit_dir2 = os.path.join(self.retro_dir, "commit2")
        os.makedirs(self.commit_dir1)
        os.makedirs(self.commit_dir2)

        # Create dummy playwright.xml and vitest.log files in each commit directory
        for commit_dir in [self.commit_dir1, self.commit_dir2]:
            tool_summary_path = os.path.join(commit_dir, "tool-summary")
            os.makedirs(tool_summary_path)
            with open(os.path.join(tool_summary_path, "playwright.xml"), "w") as f:
                f.write(
                    """
                    <testsuites>
                        <testsuite><testcase name='test1' time='0.1'/></testsuite>
                    </testsuites>
                    """
                )
            with open(os.path.join(tool_summary_path, "vitest.log"), "w") as f:
                f.write(
                    """
                    <testsuites>
                        <testsuite><testcase name='test2' time='0.2'/></testsuite>
                    </testsuites>
                    """
                )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_process_retro(self):
        # Call process_retro with the correct path
        process_retro(os.path.join(self.temp_dir.name, "retros", "test_retro"))

        # Assert that playwright.csv and vitest.csv files were created
        # in each commit directory
        for commit_dir in [self.commit_dir1, self.commit_dir2]:
            tool_summary_dir = os.path.join(commit_dir, "tool-summary")
            self.assertTrue(
                os.path.exists(os.path.join(tool_summary_dir, "playwright.csv"))
            )
            self.assertTrue(
                os.path.exists(os.path.join(tool_summary_dir, "vitest.csv"))
            )
