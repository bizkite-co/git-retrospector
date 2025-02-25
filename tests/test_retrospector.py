import os
import subprocess
import tempfile
import unittest
from unittest.mock import mock_open, patch

import toml

from git_retrospector.config import Config
from git_retrospector.retrospector import (
    get_current_commit_hash,
    initialize,
    process_commit,
    run_tests,
)
from git_retrospector.runners import run_playwright, run_vitest


class TestRetrospector(unittest.TestCase):
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

    def test_get_current_commit_hash(self):
        result = get_current_commit_hash(self.repo_path)
        self.assertTrue(isinstance(result, str))
        self.assertIsNotNone(result)

    def test_initialize_creates_directory_and_config(self):
        target_name = "test_target"
        repo_under_test_path = "test_repo_path"  # Use repo_under_test_path
        output_base_dir = self.temp_dir.name  # Use the temporary directory

        initialize(target_name, repo_under_test_path, output_base_dir)

        expected_target_dir = os.path.join(output_base_dir, "retros", target_name)
        self.assertTrue(os.path.isdir(expected_target_dir))

        expected_config_path = os.path.join(expected_target_dir, "config.toml")
        self.assertTrue(os.path.isfile(expected_config_path))

        with open(expected_config_path) as f:
            config = toml.load(f)

        self.assertEqual(config["name"], target_name)
        self.assertEqual(config["repo_under_test_path"], repo_under_test_path)
        self.assertEqual(
            config["test_result_dir"],
            os.path.join(output_base_dir, "retros", target_name),
        )
        self.assertDictEqual(
            config["output_paths"],
            {
                "vitest": "test-output/vitest.xml",
                "playwright": "test-output/playwright.xml",
            },
        )

    @patch("git_retrospector.retrospector.process_commit")
    @patch("git_retrospector.retrospector.get_current_commit_hash")
    @patch("git_retrospector.retrospector.get_original_branch")
    def test_run_tests_loads_config(
        self,
        mock_get_original_branch,
        mock_get_current_commit_hash,
        mock_process_commit,
    ):
        # Mock the return values of the mocked functions
        mock_get_original_branch.return_value = "main"

        # Use a side effect to conditionally mock get_current_commit_hash
        def mock_commit_hash(repo_path):
            if repo_path == "/path/to/target_repo":
                return "abcdef"  # Mock commit hash for the target repo
            else:
                return get_current_commit_hash(repo_path)  # Original function

        mock_get_current_commit_hash.side_effect = mock_commit_hash

        # Create a temporary directory and a mock config.toml file
        with tempfile.TemporaryDirectory() as temp_dir:
            target_name = "test_target"
            target_dir = os.path.join(temp_dir, "retros", target_name)
            os.makedirs(target_dir)
            config_file_path = os.path.join(target_dir, "config.toml")
            config_data = {
                "name": target_name,
                "repo_under_test_path": "/path/to/target_repo",
                "test_result_dir": os.path.join(temp_dir, "retros", target_name),
                "output_paths": {
                    "vitest": "test-output/vitest.xml",
                    "playwright": "test-output/playwright.xml",
                },
            }
            with open(config_file_path, "w") as f:
                toml.dump(config_data, f)

            # Change the working directory to the temp dir
            os.chdir(temp_dir)
            config = Config(**config_data)

            with patch("subprocess.run") as mock_run:
                # Mock the behavior of subprocess.run for the git rev-parse command
                mock_run.return_value.stdout = "abcdef\n"  # Mock commit hash

                # Call run_tests with the test target name
                run_tests(target_name, iteration_count=1)

                # Assert that process_commit was called with the correct arguments
                mock_process_commit.assert_called_once_with(
                    config_data["repo_under_test_path"],
                    "abcdef",
                    config.test_result_dir / "test-output",
                    "main",
                    config,
                )

    @patch("git_retrospector.retrospector.run_playwright")
    @patch("git_retrospector.retrospector.run_vitest")
    def test_process_commit(self, mock_run_vitest, mock_run_playwright):
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock config.toml file
            target_name = "test_target"
            target_dir = os.path.join(temp_dir, "retros", target_name)
            os.makedirs(target_dir)
            config_file_path = os.path.join(target_dir, "config.toml")
            config_data = {
                "name": target_name,
                "repo_under_test_path": "/path/to/target_repo",
                "test_result_dir": os.path.join(temp_dir, "retros", target_name),
                "output_paths": {  # Add output paths for consistency
                    "vitest": "test-output/vitest.xml",
                    "playwright": "test-output/playwright.xml",
                },
            }
            with open(config_file_path, "w") as f:
                toml.dump(config_data, f)

            # Create a mock commit hash and output directory
            commit_hash = "abcdef"

            config = Config(**config_data)
            output_dir_for_commit = config.test_result_dir / "test-output" / commit_hash

            # Call process_commit
            process_commit(
                config.repo_under_test_path,
                commit_hash,
                str(config.test_result_dir),
                "main",
                config,
            )

            # Assert that the commit-specific output directory was created
            self.assertTrue(os.path.isdir(output_dir_for_commit))

            # Assert that run_vitest and run_playwright were called with the correct
            # arguments
            mock_run_vitest.assert_called_once_with(
                config.repo_under_test_path, str(output_dir_for_commit), config
            )
            mock_run_playwright.assert_called_once_with(
                config.repo_under_test_path, str(output_dir_for_commit), config
            )

    @patch("subprocess.run")
    def test_run_vitest_constructs_command(self, mock_run):
        target_repo = "/path/to/target_repo"
        output_dir = "/path/to/output/dir"
        config_data = {"output_paths": {"vitest": "vitest.xml"}}
        config = Config(
            **config_data,
            name="test",
            repo_under_test_path="test",
            test_result_dir="test",
        )

        with patch("builtins.open", mock_open(read_data=toml.dumps(config_data))):
            run_vitest(target_repo, output_dir, config)
            mock_run.assert_called_once_with(
                ["npx", "vitest", "run", "--reporter=junit"],
                cwd=target_repo,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=True,
                text=True,
            )

    @patch("subprocess.run")
    def test_run_playwright_constructs_command(self, mock_run):
        target_repo = "/path/to/target_repo"
        output_dir = "/path/to/output/dir"
        config_data = {"output_paths": {"playwright": "playwright.xml"}}
        config = Config(
            **config_data,
            name="test",
            repo_under_test_path="test",
            test_result_dir="test",
        )

        with patch("builtins.open", mock_open(read_data=toml.dumps(config_data))):
            run_playwright(target_repo, output_dir, config)
            mock_run.assert_called_once_with(
                ["npx", "playwright", "test", "--reporter=junit"],
                cwd=target_repo,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=True,
                text=True,
            )

    def tearDown(self):
        self.temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
