import os
from git_retrospector.parser import process_retro
from TestConfig import BaseTest


class TestRetroProcessor(BaseTest):
    def setUp(self):
        super().setUp()
        self.commit_hash1 = "commit1"
        self.commit_hash2 = "commit2"
        self.retro.create_commit_hash_dir(self.commit_hash1)
        self.retro.create_commit_hash_dir(self.commit_hash2)

    def test_process_retro(self):

        # Create dummy playwright.xml file in each commit directory
        for commit_hash in [self.commit_hash1, self.commit_hash2]:
            with open(self.retro.get_playwright_xml_path(commit_hash), "w") as f:
                f.write(
                    """
                    <testsuites>
                        <testsuite><testcase name='test1' time='0.1'/></testsuite>
                    </testsuites>
                    """
                )
            with open(self.retro.get_vitest_log_path(commit_hash), "w") as f:
                f.write(
                    """
                    <testsuites>
                        <testsuite><testcase name='test2' time='0.2'/></testsuite>
                    </testsuites>
                    """
                )

        # Call process_retro with the retro
        process_retro(self.retro)

        # Assert that playwright.csv and vitest.csv files were created
        # in each commit directory
        for commit_hash in [self.commit_hash1, self.commit_hash2]:
            self.assertTrue(
                self.retro.path_exists(
                    os.path.relpath(
                        self.retro.get_playwright_csv_path(commit_hash),
                        self.retro.get_retro_dir(),
                    )
                )
            )
            self.assertTrue(
                self.retro.path_exists(
                    os.path.relpath(
                        self.retro.get_vitest_csv_path(commit_hash),
                        self.retro.get_retro_dir(),
                    )
                )
            )
