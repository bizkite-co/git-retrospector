import unittest
import tempfile
import subprocess
import os
import toml
from unittest.mock import patch, mock_open
from git_retrospector.retrospector import get_current_commit_hash, initialize, run_tests


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
        source_dir = "test_source_dir"
        output_base_dir = self.temp_dir.name  # Use the temporary directory

        initialize(target_name, source_dir, output_base_dir)

        expected_target_dir = os.path.join(output_base_dir, "retros", target_name)
        self.assertTrue(os.path.isdir(expected_target_dir))

        expected_config_path = os.path.join(expected_target_dir, "config.toml")
        self.assertTrue(os.path.isfile(expected_config_path))

        with open(expected_config_path, "r") as f:
            config = toml.load(f)

        self.assertEqual(config["name"], target_name)
        self.assertEqual(config["source_dir"], source_dir)
        self.assertEqual(config["test_result_dir"], os.path.join(expected_target_dir, "test-result-dir"))
        self.assertDictEqual(config["output_paths"], {
            "vitest": "test-output/vitest.xml",
            "playwright": "test-output/playwright.xml",
        })
        self.assertEqual(config["test_output_dir"], "test-output")

    @patch("git_retrospector.retrospector.process_commit")
    @patch("git_retrospector.retrospector.get_current_commit_hash")
    @patch("git_retrospector.retrospector.get_original_branch")
    def test_run_tests_loads_config(
        self, mock_get_original_branch, mock_get_current_commit_hash, mock_process_commit
    ):
        # Mock the return values of the mocked functions
        mock_get_original_branch.return_value = "main"

        # Use a side effect to conditionally mock get_current_commit_hash
        def mock_commit_hash(repo_path):
            if repo_path == "/path/to/target_repo":
                return "abcdef"  # Mock commit hash for the target repo
            else:
                return get_current_commit_hash(repo_path) # Original function for other calls

        mock_get_current_commit_hash.side_effect = mock_commit_hash

        # Create a temporary directory and a mock config.toml file
        with tempfile.TemporaryDirectory() as temp_dir:
            target_name = "test_target"
            target_dir = os.path.join(temp_dir, "retros", target_name)
            os.makedirs(target_dir)
            config_file_path = os.path.join(target_dir, "config.toml")
            config_data = {
                "name": target_name,
                "source_dir": "/path/to/target_repo",
                "test_output_dir": "test-output",
            }
            with open(config_file_path, "w") as f:
                toml.dump(config_data, f)

            # Change the working directory to the temp dir
            os.chdir(temp_dir)

            with patch('subprocess.run') as mock_run:
                # Mock the behavior of subprocess.run for the git rev-parse command
                mock_run.return_value.stdout = "abcdef\n" # Mock commit hash

                # Call run_tests with the test target name
                run_tests(target_name, iteration_count=1)

                # Assert that process_commit was called with the correct arguments
                mock_process_commit.assert_called_once_with(
                    config_data["source_dir"],
                    "abcdef",
                    os.path.join("retros", target_name, config_data["test_output_dir"]),
                    "main",
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
                "source_dir": "/path/to/target_repo",
                "test_output_dir": "test-output",
                "output_paths": {  # Add output paths for consistency
                    "vitest": "test-output/vitest.xml",
                    "playwright": "test-output/playwright.xml",
                },
            }
            with open(config_file_path, "w") as f:
                toml.dump(config_data, f)

            # Create a mock commit hash and output directory
            commit_hash = "abcdef"

            output_dir = os.path.join(temp_dir, "retros", target_name)

            # Call process_commit
            process_commit("/path/to/target_repo", commit_hash, output_dir, "main")

            # Assert that the commit-specific output directory was created
            expected_output_dir = os.path.join(output_dir, "test-output", commit_hash)
            self.assertTrue(os.path.isdir(expected_output_dir))

            # Assert that run_vitest and run_playwright were called with the correct arguments
            mock_run_vitest.assert_called_once_with("/path/to/target_repo", expected_output_dir)
            mock_run_playwright.assert_called_once_with("/path/to/target_repo", expected_output_dir)

    @patch("subprocess.run")
    def test_run_vitest_constructs_command(self, mock_run):
        target_repo = "/path/to/target_repo"
        output_dir = "/path/to/output/dir"
        config_data = {
            "output_paths": {
                "vitest": "vitest.xml"
            }
        }

        with patch('builtins.open', mock_open(read_data=toml.dumps(config_data))) as mocked_file:
            run_vitest(target_repo, output_dir)
            mock_run.assert_called_once_with(
                [
                    "npx",
                    "vitest",
                    "run",
                    "--reporter=junit",
                    f"--outputFile={os.path.join(output_dir, 'vitest.xml')}",
                ],
                cwd=os.getcwd(),
                stdout=ANY,  # Don't need to be specific about the file object
                stderr=subprocess.STDOUT,
                check=True,
                text=True,
            )

    @patch("subprocess.run")
    def test_run_playwright_constructs_command(self, mock_run):
        target_repo = "/path/to/target_repo"
        output_dir = "/path/to/output/dir"
        config_data = {
            "output_paths": {
                "playwright": "playwright.xml"
            }
        }

        with patch('builtins.open', mock_open(read_data=toml.dumps(config_data))) as mocked_file:
            run_playwright(target_repo, output_dir)
            mock_run.assert_called_once_with(
                ["npx", "playwright", "test", "--reporter=junit"],
                cwd=os.getcwd(),
                env={**os.environ, 'PLAYWRIGHT_JUNIT_OUTPUT_NAME': os.path.join(output_dir, 'playwright.xml')},
                stdout=ANY,
                stderr=subprocess.STDOUT,
                check=True,
                text=True,
            )

    def tearDown(self):
        self.temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
