#!/usr/bin/env python3

import unittest
import subprocess
from pathlib import Path
from git_retrospector.diff_utils import generate_diff


class TestGenerateDiff(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the test
        self.test_dir = Path("test_repo")
        self.test_dir.mkdir(exist_ok=True)

        # Initialize a git repository
        subprocess.run(
            ["git", "init"], cwd=self.test_dir, check=True, capture_output=True
        )

        # Create an initial file and commit
        with open(self.test_dir / "file1.txt", "w") as f:
            f.write("Initial content")
        subprocess.run(
            ["git", "add", "file1.txt"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
        )
        self.commit1 = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=self.test_dir,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        # Modify the file and commit again
        with open(self.test_dir / "file1.txt", "w") as f:
            f.write("Modified content")
        subprocess.run(
            ["git", "add", "file1.txt"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Second commit"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
        )
        self.commit2 = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=self.test_dir,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def tearDown(self):
        # Clean up the temporary directory
        subprocess.run(
            ["rm", "-rf", str(self.test_dir)], check=True, capture_output=True
        )

    def test_generate_diff(self):
        # Create a temporary output file
        output_file = self.test_dir / "test_diff.diff"

        # Call generate_diff
        generate_diff(str(self.test_dir), self.commit1, self.commit2, str(output_file))

        # Check if the output file exists
        self.assertTrue(output_file.exists())

        # Generate the expected diff using git diff
        result = subprocess.run(
            ["git", "diff", self.commit1, self.commit2],
            cwd=self.test_dir,
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
