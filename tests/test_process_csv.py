import unittest
import csv
import os
import tempfile
from unittest.mock import MagicMock
from git_retrospector.retrospector import process_csv_files


class TestProcessCSVFiles(unittest.TestCase):
    def test_process_csv_files(self):
        # Create temporary CSV files
        with tempfile.TemporaryDirectory() as temp_dir:
            playwright_csv = os.path.join(temp_dir, "playwright.csv")
            vitest_csv = os.path.join(temp_dir, "vitest.csv")

            with open(playwright_csv, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Test Name", "Result", "Error", "Stack Trace"])
                writer.writerow(["test1", "failed", "Error message 1", "Stack 1"])

            with open(vitest_csv, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Test Name", "Result", "Error", "Stack Trace"])
                writer.writerow(["test2", "failed", "Error message 2", "Stack 2"])

            # Create a mock repository
            mock_repo = MagicMock()

            # Call the function
            process_csv_files(mock_repo, playwright_csv, vitest_csv)

            # Assert that create_issue was called twice
            self.assertEqual(mock_repo.create_issue.call_count, 2)

            # Assert calls with correct arguments
            mock_repo.create_issue.assert_any_call(
                title="test1",
                body="Error: Error message 1\nStack Trace: Stack 1\n",
            )
            mock_repo.create_issue.assert_any_call(
                title="test2",
                body="Error: Error message 2\nStack Trace: Stack 2\n",
            )


if __name__ == "__main__":
    unittest.main()
