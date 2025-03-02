#!/usr/bin/env python3

import unittest
import subprocess
from git_retrospector.diff_utils import generate_diff
from TestConfig import BaseTest
from pathlib import Path


class TestGenerateDiff(BaseTest):

    def setUp(self):
        super().setUp()

        # Initialize a git repository
        subprocess.run(
            ["git", "init"], cwd=self.temp_dir, check=True, capture_output=True
        )

        # Create an initial file and commit
        with open(Path(self.temp_dir) / "file1.txt", "w") as f:
            f.write("Initial content")
        subprocess.run(
            ["git", "add", "file1.txt"],
            cwd=self.temp_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.temp_dir,
            check=True,
            capture_output=True,
        )
        self.commit1 = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=self.temp_dir,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        # Modify the file and commit again
        with open(Path(self.temp_dir) / "file1.txt", "w") as f:
            f.write("Modified content")
        subprocess.run(
            ["git", "add", "file1.txt"],
            cwd=self.temp_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Second commit"],
            cwd=self.temp_dir,
            check=True,
            capture_output=True,
        )
        self.commit2 = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=self.temp_dir,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    # def tearDown(self):
    #     # Clean up the temporary directory
    #     shutil.rmtree(self.test_dir)

    def test_generate_diff(self):
        # Create a temporary output file
        output_file = Path(self.temp_dir) / "test_diff.diff"

        # Call generate_diff
        generate_diff(
            self.retro, str(self.temp_dir), self.commit1, self.commit2, str(output_file)
        )

        # Check if the output file exists
        self.assertTrue(output_file.exists())

        # Generate the expected diff using git diff
        result = subprocess.run(
            ["git", "diff", self.commit1, self.commit2],
            cwd=self.temp_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        expected_diff = result.stdout

        # Compare the generated diff with the expected diff
        with open(output_file) as f:
            actual_diff = f.read()
        self.assertEqual(actual_diff, expected_diff)


if __name__ == "__main__":
    unittest.main()
