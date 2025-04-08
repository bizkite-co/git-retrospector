import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, call, mock_open
from click.testing import CliRunner

# Assuming retrospector.py is in the same directory or in PYTHONPATH
from git_retrospector.retrospector import (
    cli,
)
from git_retrospector.retro import Retro  # Import TestRunner

# Mock the config data that toml.load would return
MOCK_CONFIG_DATA = {
    "name": "test_target",
    # This will be resolved to absolute
    # in Retro init
    "remote_repo_path": "/mock/repo/path",
    "test_output_dir": "retros/test_target/test-output",  # Relative path
    "target_branch": "main",
    "iterations": 10,  # Default iterations in config
    "date_format": "%Y-%m-%d",
    "output_format": "csv",
    "include_diff": False,
    "include_stats": True,
    "template_path": "path/to/template.md",
    "issue_title_template": "Retro Issue: {summary}",
    "issue_label": "retrospection",
    "auto_assign": True,
    "github_remote": "",
    "github_repo_name": "",
    "github_repo_owner": "",
    "github_project_name": "",
    "github_project_number": 0,
    "github_project_owner": "",
    "test_result_dir": "",
    "test_runners": [],  # Ensure this matches the expected type (list)
}


class TestRetrospectorCLI(unittest.TestCase):
    def setUp(self):
        self.base_temp_dir = tempfile.mkdtemp()
        self.mock_retro_base = Path(self.base_temp_dir)
        self.mock_repo_path_abs = self.mock_retro_base / "mock_repo"
        self.mock_repo_path_abs.mkdir()
        self.target_name = "test_target"  # Define target name used in test
        self.mock_output_dir_relative = MOCK_CONFIG_DATA["test_output_dir"]
        self.expected_abs_output_dir = (
            self.mock_retro_base / self.mock_output_dir_relative
        )

        self.runner = CliRunner()
        self.cwd_patcher = patch("pathlib.Path.cwd", return_value=self.mock_retro_base)
        self.mock_cwd = self.cwd_patcher.start()
        # Mock Path.mkdir directly as it's called by the code
        self.path_mkdir_patcher = patch("pathlib.Path.mkdir")
        self.mock_path_mkdir = self.path_mkdir_patcher.start()
        # Keep os.makedirs mock for other potential uses if needed, or remove if unused
        self.makedirs_patcher = patch("os.makedirs")
        self.mock_makedirs = self.makedirs_patcher.start()

    def tearDown(self):
        shutil.rmtree(self.base_temp_dir)
        self.cwd_patcher.stop()
        self.path_mkdir_patcher.stop()  # Stop Path.mkdir mock
        self.makedirs_patcher.stop()

    @patch("git_retrospector.retrospector.toml.load")
    @patch("git_retrospector.retrospector.Retro.initialize")
    def test_init_command(self, mock_retro_initialize, mock_toml_load):
        target_name = "new_target"
        repo_path_arg = str(self.mock_repo_path_abs)
        result = self.runner.invoke(cli, ["init", target_name, repo_path_arg])
        self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        mock_retro_initialize.assert_called_once()

    # Mock Retro class directly where it's instantiated in retrospector.py
    @patch("git_retrospector.retrospector.Retro")
    @patch("git_retrospector.retrospector.json.dump")
    @patch("builtins.open", new_callable=mock_open)
    # Mock process_commit where it's looked up in the retrospector module
    @patch("git_retrospector.retrospector.process_commit")
    @patch("git_retrospector.retrospector.get_commit_list")
    # @patch("git_retrospector.retrospector.toml.load") # Mocked via Retro mock
    @patch("git_retrospector.retrospector.analyze_test_results")
    @patch(
        "git_retrospector.retrospector.get_origin_branch_or_commit", return_value="main"
    )
    @patch("git_retrospector.retrospector.subprocess.run")
    def test_run_command(
        self,
        mock_subprocess_run,
        mock_get_origin,
        mock_analyze,
        # mock_toml_load, # Removed
        mock_get_commit_list,
        mock_process_commit,  # Updated mock target
        mock_open_file,
        mock_json_dump,
        mock_retro_class,  # Mock for the Retro class itself
    ):
        # --- Test Setup ---
        target_name = self.target_name
        iterations_cli = 5
        mock_repo_path_for_assertion = str(self.mock_repo_path_abs.resolve())
        expected_abs_output_dir = self.expected_abs_output_dir
        expected_manifest_path = expected_abs_output_dir / "commit_manifest.json"
        # expected_config_path_rel = Path("retros") / target_name / "retro.toml"
        # expected_config_path_abs = self.mock_retro_base / expected_config_path_rel

        # Configure the mock Retro instance
        mock_retro_instance = MagicMock(spec=Retro)
        mock_retro_instance.name = target_name
        mock_retro_instance.remote_repo_path = Path(mock_repo_path_for_assertion)
        mock_retro_instance.local_test_output_dir_full = str(expected_abs_output_dir)
        mock_retro_instance.get_test_output_dir.return_value = expected_abs_output_dir
        mock_retro_class.return_value = mock_retro_instance

        # Mock commit data
        mock_commits = [
            {"hash": "hash1", "date": "date1", "summary": "summary1"},
            {"hash": "hash2", "date": "date2", "summary": "summary2"},
        ]
        mock_get_commit_list.return_value = mock_commits

        # --- Run Command ---
        result = self.runner.invoke(
            cli, ["run", target_name, "--iterations", str(iterations_cli)]
        )

        # --- Assertions ---
        self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")

        # 1. Assert Retro class was instantiated
        mock_retro_class.assert_called()

        # 2. Assert get_commit_list called correctly
        mock_get_commit_list.assert_called_once_with(
            str(mock_retro_instance.remote_repo_path), iterations_cli
        )

        # 3. Assert directory creation for manifest using Path.mkdir mock
        self.mock_path_mkdir.assert_any_call(parents=True, exist_ok=True)

        # 4. Assert commit_manifest.json written correctly
        manifest_open_call = None
        resolved_expected_manifest_path = expected_manifest_path.resolve()
        for call_args in mock_open_file.call_args_list:
            if (
                Path(call_args[0][0]).resolve() == resolved_expected_manifest_path
                and call_args[0][1] == "w"
            ):
                manifest_open_call = call_args
                break
        self.assertIsNotNone(
            manifest_open_call,
            f"""Manifest file {
                resolved_expected_manifest_path
                } was not opened for writing ('w'). Calls: {
                mock_open_file.call_args_list}""",
        )

        # Assert json.dump called once and inspect arguments
        mock_json_dump.assert_called_once()
        dump_args, dump_kwargs = mock_json_dump.call_args
        self.assertEqual(dump_args[0], mock_commits)  # Check the data argument
        self.assertIs(
            dump_args[1], mock_open_file.return_value
        )  # Check file handle object identity
        self.assertEqual(
            dump_kwargs.get("indent"), 2
        )  # Check the indent keyword argument

        # 5. Assert process_commit (mocked in retrospector namespace) was
        # called
        # Note: The actual call happens inside process_single_commit, which
        # we are NOT mocking here.
        # We rely on process_single_commit calling the mocked process_commit.
        self.assertEqual(mock_process_commit.call_count, len(mock_commits))
        expected_calls = []
        for commit in mock_commits:
            # These are the arguments process_single_commit *should* pass
            # to process_commit
            expected_calls.append(
                call(
                    # Path object from mock Retro
                    remote_repo_path=mock_retro_instance.remote_repo_path,
                    commit_hash=commit["hash"],
                    test_output_dir=str(
                        expected_abs_output_dir
                    ),  # Absolute path string
                    origin_branch="main",
                    retro=mock_retro_instance,  # The mock Retro instance
                )
            )
        # mock_process_commit.assert_has_calls(expected_calls, any_order=False)
        # Optional detailed check

        # 6. Assert analyze_test_results called
        mock_analyze.assert_called_once_with(mock_retro_instance)

        # 7. Assert final git checkout called
        mock_subprocess_run.assert_called_with(
            ["git", "checkout", "--force", "main"],
            cwd=str(mock_retro_instance.remote_repo_path),
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
