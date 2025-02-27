import unittest
from unittest.mock import patch
import os
import tempfile
import subprocess
import toml
import time
import logging
from git_retrospector.retrospector import (
    run_tests,
    analyze_test_results,
    find_test_summary_files,
    count_failed_tests,
    load_config_for_retro,
    get_user_confirmation,
)


class TestRetrospector(unittest.TestCase):
    def setUp(self):
        print("Setting up TestRetrospector")  # noqa: T201

    @patch("git_retrospector.retrospector.process_commit")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    def test_run_tests(self, mock_open, mock_process_commit):
        logging.basicConfig(level=logging.DEBUG)
        with tempfile.TemporaryDirectory() as temp_repo_path:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create a test retro name
                retro_name = "test_retro"

                # Create a mock config dictionary
                mock_config_data = {
                    "name": retro_name,
                    "repo_under_test_path": temp_repo_path,
                    "test_result_dir": temp_dir,
                    "output_paths": {
                        "vitest": "test-output/vitest.xml",
                        "playwright": "test-output/playwright.xml",
                    },
                }

                # Configure the mock open to return the mock config data,
                # including the name
                mock_open.return_value.read.return_value = toml.dumps(mock_config_data)

                # Initialize a git repo in the temp dir
                subprocess.run(
                    ["git", "init"],
                    cwd=temp_repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    ["git", "commit", "--allow-empty", "-m", "Initial commit"],
                    cwd=temp_repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                # Create a second commit
                with open(os.path.join(temp_repo_path, "file1.txt"), "w") as f:
                    f.write("Initial content")
                time.sleep(0.1)  # Add a short delay
                subprocess.run(["git", "add", "."], cwd=temp_repo_path, check=True)
                subprocess.run(
                    ["git", "commit", "--allow-empty", "-m", "Second commit"],
                    cwd=temp_repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                # Create the directory structure
                retro_dir = os.path.join("retros", retro_name)
                os.makedirs(retro_dir, exist_ok=True)

                logging.debug("Calling run_tests")
                run_tests(retro_name, 2)

                self.assertEqual(mock_process_commit.call_count, 2)

    @patch("builtins.print")
    def test_run_tests_no_config(self, mock_print):
        # Call run_tests with a non-existent target name
        run_tests("nonexistent_target", 2)

        # Assert that the expected error message is printed
        mock_print.assert_called_with(
            "Error: Config file not found: retros/nonexistent_target/config.toml\n"
            "Please run: './retrospector.py init nonexistent_target <target_repo_path>'"
        )

    @patch("git_retrospector.retrospector.generate_commit_diffs")
    @patch("git_retrospector.parser.process_retro")
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

            with self.assertRaises(FileNotFoundError):
                find_test_summary_files("nonexistent_dir")

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
