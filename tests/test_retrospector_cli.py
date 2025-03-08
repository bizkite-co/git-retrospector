import unittest
import tempfile
import os
import shutil
from click.testing import CliRunner

# Assuming retrospector.py is in the same directory or in PYTHONPATH
from git_retrospector.retrospector import (
    cli,
)  # Import the cli function from your script
from git_retrospector.git_retrospector import Retro


class TestRetrospectorCLI(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)

        # Initialize a Retro object for testing
        self.retro = Retro(
            name="test_retro",
            remote_repo_path=self.repo_dir,
            test_output_dir=os.path.join(self.temp_dir, "test-output"),
        )
        self.runner = CliRunner()  # Initialize CliRunner here

    def tearDown(self):
        # Clean up the temporary directory after each test
        shutil.rmtree(self.temp_dir)

    def test_init_command(self):
        # Test the 'init' command
        result = self.runner.invoke(
            cli, ["init", "test_target", "/path/to/target/repo"]
        )
        self.assertEqual(
            result.exit_code, 0
        )  # Check if the command executed successfully
        # Add more assertions here to check if the command had the expected effect
        # For example, check if the necessary files/directories were created

    # Add more test methods for other commands like 'run', 'issues', etc.
