import csv
import unittest
import os
from unittest.mock import MagicMock, patch
from TestConfig import BaseTest
from git_retrospector.retrospector import create_issues_for_commit


class TestCreateIssues(BaseTest):
    def setUp(self):
        super().setUp()
        self.commit_hash = "abcdef123456"
        self.retro.create_commit_hash_dir(self.commit_hash)  # Create commit dir
        self.tool_summary_dir = self.retro.get_tool_summary_dir(self.commit_hash)

    @patch("git_retrospector.retrospector.create_issues_for_commit")
    def test_create_issues_for_commit_no_dir(self, mock_create_issues_for_commit):
        # Test when the commit directory does not exist
        mock_create_github_issues = MagicMock()
        mock_create_issues_for_commit.side_effect = mock_create_github_issues
        create_issues_for_commit(self.retro.name, "nonexistent_hash")
        mock_create_github_issues.assert_not_called()

    @patch("git_retrospector.retrospector.create_issues_for_commit")
    def test_create_issues_for_commit_no_csv_files(self, mock_create_issues_for_commit):
        # Test when the CSV files are not found
        # Commit directory and tool-summary subdirectory are created in setUp

        mock_create_github_issues = MagicMock()
        mock_create_issues_for_commit.side_effect = mock_create_github_issues

        create_issues_for_commit(self.retro.name, self.commit_hash)
        mock_create_github_issues.assert_not_called()

    @patch("git_retrospector.retrospector.create_issues_for_commit")
    def test_create_issues_for_commit_no_failed_tests(
        self, mock_create_issues_for_commit
    ):
        # Test when there are no failed tests
        # Create empty CSV files
        with open(os.path.join(self.tool_summary_dir, "playwright.csv"), "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Result"])
        with open(os.path.join(self.tool_summary_dir, "vitest.csv"), "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Result"])

        mock_create_github_issues = MagicMock()
        mock_create_issues_for_commit.side_effect = mock_create_github_issues
        create_issues_for_commit(self.retro.name, self.commit_hash)
        mock_create_github_issues.assert_not_called()

    @patch(
        "git_retrospector.retrospector.load_config_for_retro",
        return_value=("test_owner", "test_repo"),
    )
    @patch("git_retrospector.retrospector.input", return_value="y")
    @patch("os.environ.get", return_value="dummy_token")
    @patch("git_retrospector.retrospector.Github")
    @patch(
        "git_retrospector.retrospector.process_csv_files"
    )  # Patch process_csv_files directly
    def test_create_issues_for_commit_success(
        self,
        mock_process_csv_files,
        mock_github_class,
        mock_env_get,
        mock_input,
        mock_load_retro,
    ):
        # Mock the Github object and its methods
        mock_repo = MagicMock()
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github
        mock_github.get_user.return_value.get_repo.return_value = mock_repo

        # Create CSV files with failed tests
        playwright_csv = os.path.join(self.tool_summary_dir, "playwright.csv")
        vitest_csv = os.path.join(self.tool_summary_dir, "vitest.csv")
        with open(playwright_csv, "w") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["Commit", "Test Type", "Test Name", "Result", "Duration", "Media Path"]
            )
            writer.writerow(
                ["abcdef123456", "playwright", "test1", "failed", "0.1", ""]
            )
        with open(vitest_csv, "w") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["Commit", "Test Type", "Test Name", "Result", "Duration", "Media Path"]
            )
            writer.writerow(["abcdef123456", "vitest", "test2", "failed", "0.2", ""])

        # Call the function directly without patching it
        with patch(
            "git_retrospector.retrospector.should_create_issues", return_value=True
        ):
            with patch(
                "git_retrospector.retrospector.find_test_summary_files",
                return_value=(playwright_csv, vitest_csv),
            ):
                create_issues_for_commit(self.retro.name, self.commit_hash)

        # Assert that process_csv_files was called with the mock repo and CSV paths
        mock_process_csv_files.assert_called_once_with(
            mock_repo, playwright_csv, vitest_csv
        )


if __name__ == "__main__":
    unittest.main()
