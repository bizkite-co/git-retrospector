import csv
import os
import unittest
from unittest.mock import MagicMock, patch

from git_retrospector.retrospector import create_issues_for_commit


class TestCreateIssues(unittest.TestCase):
    def setUp(self):
        self.retro_name = "test_retro"
        self.commit_hash = "abcdef123456"
        self.commit_dir = os.path.join(
            "retros", self.retro_name, "test-output", self.commit_hash
        )
        self.tool_summary_dir = os.path.join(self.commit_dir, "tool-summary")
        # Ensure the base "retros" directory exists
        os.makedirs("retros", exist_ok=True)

    def tearDown(self):
        # Cleanup directories only if they exist
        if os.path.exists(self.tool_summary_dir):
            import shutil

            shutil.rmtree(self.tool_summary_dir)
        if os.path.exists(self.commit_dir):
            import shutil

            shutil.rmtree(self.commit_dir)

    @patch("git_retrospector.retrospector.Github")
    def test_create_issues_for_commit_no_dir(self, mock_github):
        # Test when the commit directory does not exist
        create_issues_for_commit(self.retro_name, self.commit_hash)
        mock_github.assert_not_called()

    @patch("git_retrospector.retrospector.Github")
    def test_create_issues_for_commit_no_csv_files(self, mock_github):
        # Test when the CSV files are not found
        # Create the commit directory *and* the tool-summary subdirectory
        os.makedirs(self.tool_summary_dir)

        create_issues_for_commit(self.retro_name, self.commit_hash)
        mock_github.assert_not_called()

    @patch("git_retrospector.retrospector.Github")
    def test_create_issues_for_commit_no_failed_tests(self, mock_github):
        # Test when there are no failed tests
        os.makedirs(self.tool_summary_dir)

        # Create empty CSV files
        with open(os.path.join(self.tool_summary_dir, "playwright.csv"), "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Result"])
        with open(os.path.join(self.tool_summary_dir, "vitest.csv"), "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Result"])

        create_issues_for_commit(self.retro_name, self.commit_hash)
        mock_github.assert_not_called()

    @patch("git_retrospector.retrospector.input", return_value="n")
    @patch("git_retrospector.retrospector.Github")
    def test_create_issues_for_commit_user_denies(self, mock_github, mock_input):

        # Test when the user denies creating issues
        os.makedirs(self.tool_summary_dir)

        # Create CSV files with a failed test
        with open(os.path.join(self.tool_summary_dir, "playwright.csv"), "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Result"])
            writer.writerow(["test1", "failed"])
        with open(os.path.join(self.tool_summary_dir, "vitest.csv"), "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Result"])
            writer.writerow(["test2", "failed"])

        create_issues_for_commit(self.retro_name, self.commit_hash)
        mock_github.assert_not_called()

    @patch("os.environ.get", return_value="dummy_token")
    @patch("git_retrospector.retrospector.Github")
    @patch("git_retrospector.retrospector.input", return_value="y")
    @patch(
        "git_retrospector.retrospector.load_config_for_retro",
        return_value=("test_owner", "test_repo"),
    )
    def test_create_issues_for_commit_success(
        self, mock_load_config, mock_input, mock_github, mock_env_get
    ):

        # Test successful issue creation
        os.makedirs(self.tool_summary_dir)

        # Create CSV files with failed tests
        with open(os.path.join(self.tool_summary_dir, "playwright.csv"), "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Result", "Error", "Stack Trace"])
            writer.writerow(["test1", "failed", "Error message 1", "Stack 1"])
        with open(os.path.join(self.tool_summary_dir, "vitest.csv"), "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Result", "Error", "Stack Trace"])
            writer.writerow(["test2", "failed", "Error message 2", "Stack 2"])

        # Mock the Github object and its methods
        mock_repo = MagicMock()
        mock_github.return_value.get_user.return_value.get_repo.return_value = mock_repo

        create_issues_for_commit(self.retro_name, self.commit_hash)

        # Assert that create_issue was called twice (once for each failed test)
        self.assertEqual(mock_repo.create_issue.call_count, 2)

        # Check the arguments passed to create_issue
        mock_repo.create_issue.assert_any_call(
            title="test1",
            body="Error: Error message 1\nStack Trace: Stack 1\n",
        )
        mock_repo.create_issue.assert_any_call(
            title="test2",
            body="Error: Error message 2\nStack Trace: Stack 2\n",
        )


if __name__ == "__main__":
    unittest.main()
    unittest.main()
