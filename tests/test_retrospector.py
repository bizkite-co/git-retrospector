import unittest
from unittest.mock import patch
import os
import tempfile
from git_retrospector.retrospector import (
    run_tests,
    analyze_test_results,
    find_test_summary_files,
    count_failed_tests,
    load_config_for_retro,
    get_user_confirmation,
)


class TestRetrospector(unittest.TestCase):
    @patch("git_retrospector.retrospector.process_commit")
    @patch("git_retrospector.retrospector.get_current_commit_hash")
    @patch("git_retrospector.retrospector.get_origin_branch_or_commit")
    @patch("git_retrospector.retrospector.Config")
    @patch(
        "builtins.open",
        new_callable=unittest.mock.mock_open,
        read_data=(
            "[retros]\nrepo_under_test_path = '/path/to/repo'\n"
            "test_result_dir = '/path/to/results'"
        ),
    )
    def test_run_tests(
        self,
        mock_open,
        mock_config,
        mock_get_origin,
        mock_get_current,
        mock_process_commit,
    ):
        mock_config.return_value.repo_under_test_path = "/path/to/repo"
        mock_config.return_value.test_result_dir = "/path/to/results"
        mock_get_origin.return_value = "main"
        mock_get_current.return_value = "1234567"

        run_tests("test_target", 2)

        self.assertEqual(mock_process_commit.call_count, 2)

    @patch("git_retrospector.retrospector.generate_commit_diffs")
    @patch("git_retrospector.retrospector.process_retro")
    def test_analyze_test_results(self, mock_process_retro, mock_generate_diffs):
        analyze_test_results("test_retro")
        mock_process_retro.assert_called_once_with("test_retro")
        mock_generate_diffs.assert_called_once_with(
            os.path.join("retros", "test_retro")
        )

    def test_find_test_summary_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tool_summary_dir = os.path.join(temp_dir, "tool-summary")
            os.makedirs(tool_summary_dir)
            with open(os.path.join(tool_summary_dir, "playwright.csv"), "w") as f:
                f.write("test")
            with open(os.path.join(tool_summary_dir, "vitest.csv"), "w") as f:
                f.write("test")

            playwright_csv, vitest_csv = find_test_summary_files(temp_dir)
            self.assertIsNotNone(playwright_csv)
            self.assertIsNotNone(vitest_csv)

            playwright_csv, vitest_csv = find_test_summary_files("nonexistent_dir")
            self.assertIsNone(playwright_csv)
            self.assertIsNone(vitest_csv)

    def test_count_failed_tests(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("Test Name,Result\n")
            temp_file.write("Test1,passed\n")
            temp_file.write("Test2,failed\n")
            temp_file.close()

            failed_count = count_failed_tests(temp_file.name)
            self.assertEqual(failed_count, 1)
            os.remove(temp_file.name)

    @patch("git_retrospector.retrospector.Config")
    @patch(
        "builtins.open",
        new_callable=unittest.mock.mock_open,
        read_data=(
            "[retros]\nrepo_under_test_owner = 'test_owner'\n"
            "repo_under_test_name = 'test_repo'"
        ),
    )
    def test_load_config_for_retro(self, mock_open, mock_config):
        mock_config.return_value.repo_under_test_owner = "test_owner"
        mock_config.return_value.repo_under_test_name = "test_repo"
        owner, name = load_config_for_retro("test_retro")
        self.assertEqual(owner, "test_owner")
        self.assertEqual(name, "test_repo")

    @patch("builtins.input", return_value="y")
    def test_get_user_confirmation(self, mock_input):
        self.assertTrue(get_user_confirmation(1))
        mock_input.return_value = "n"
        self.assertFalse(get_user_confirmation(1))


if __name__ == "__main__":
    unittest.main()
