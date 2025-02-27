#!/usr/bin/env python3
import unittest
import os
import shutil
from click.testing import CliRunner
from git_retrospector.retrospector import cli


class TestRetrospectorCLI(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.test_dir = os.path.join("tests", "temp_test_retro")
        self.config_dir = os.path.join(self.test_dir, "test_target")
        self.config_file_path = os.path.join(self.config_dir, "config.toml")
        self.repo_under_test_path = os.path.join(self.test_dir, "test_repo")
        os.environ["TEST_ENVIRONMENT"] = "1"

        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.repo_under_test_path, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        del os.environ["TEST_ENVIRONMENT"]

    def test_init_command(self):
        # Test with missing arguments
        result = self.runner.invoke(cli, ["init"], catch_exceptions=True)
        self.assertNotEqual(result.exit_code, 0)

        # Test with correct arguments.
        result = self.runner.invoke(
            cli,
            ["init", "test_target", self.repo_under_test_path],
            catch_exceptions=True,
        )
        self.assertEqual(result.exit_code, 0)

    def test_run_command(self):
        # Test with missing arguments
        result = self.runner.invoke(cli, ["run"], catch_exceptions=False)
        self.assertNotEqual(result.exit_code, 0)

        # Test with correct arguments. This will fail if the config isn't set up,
        # but it tests the CLI interface.
        result = self.runner.invoke(cli, ["run", "test_target"], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)

    def test_issues_command(self):
        # Test with missing arguments
        result = self.runner.invoke(cli, ["issues"], catch_exceptions=False)
        self.assertNotEqual(result.exit_code, 0)

        # Test with correct arguments.
        # This will fail without a valid config and commit.
        result = self.runner.invoke(
            cli, ["issues", "test_target", "test_commit"], catch_exceptions=False
        )
        self.assertEqual(result.exit_code, 0)

    def test_no_command(self):
        result = self.runner.invoke(cli, [], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Usage: cli [OPTIONS] COMMAND [ARGS]...", result.output)
        self.assertIn(
            "Run tests on a range of commits and parse results.", result.output
        )


if __name__ == "__main__":
    unittest.main()
