import unittest
import tempfile
import os
import shutil
import csv
import re

from git_retrospector.retro import Retro  # Corrected import
from git_retrospector.parser import process_retro


def parse_author_line(line):
    """Parses an author line from git log output."""
    parts = line.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid author line format: {line}")
    author_info = parts[1].strip()
    match = re.match(r"(.*) <(.*)>", author_info)
    if not match:
        raise ValueError(f"Invalid author info format: {author_info}")
    return match.group(1).strip(), match.group(2).strip()


def parse_commit_line(line):
    """Parses a commit line from git log output."""
    parts = line.split()
    if len(parts) < 2 or parts[0] != "commit":
        raise ValueError(f"Invalid commit line format: {line}")
    return parts[1]


class TestParser(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)

        # Initialize a Retro object for testing
        self.retro = Retro(
            name="test_retro",
            remote_repo_path=self.repo_dir,
            test_output_dir=self.temp_dir,
        )

    def tearDown(self):
        # Clean up the temporary directory after each test
        shutil.rmtree(self.temp_dir)

    def test_parse_author_line(self):
        line = "Author: John Doe <john.doe@example.com>"
        author_name, author_email = parse_author_line(line)
        self.assertEqual(author_name, "John Doe")
        self.assertEqual(author_email, "john.doe@example.com")

    def test_parse_author_line_no_email(self):
        line = "Author: John Doe"
        with self.assertRaises(ValueError):
            parse_author_line(line)

    def test_parse_author_line_empty(self):
        line = ""
        with self.assertRaises(ValueError):
            parse_author_line(line)

    def test_parse_commit_line(self):
        line = "commit 1234567890abcdef"
        commit_hash = parse_commit_line(line)
        self.assertEqual(commit_hash, "1234567890abcdef")

    def test_parse_commit_line_no_hash(self):
        line = "commit"
        with self.assertRaises(ValueError):
            parse_commit_line(line)

    def test_parse_commit_line_empty(self):
        line = ""
        with self.assertRaises(ValueError):
            parse_commit_line(line)

    def test_process_retro_playwright(self):
        # Create a sample playwright.xml file
        commit_hash = "test_commit"
        commit_dir = os.path.join(self.retro.get_test_output_dir(commit_hash))
        os.makedirs(commit_dir, exist_ok=True)  # Only create commit dir
        playwright_xml_path = os.path.join(commit_dir, "playwright.xml")
        with open(playwright_xml_path, "w") as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
                <testsuites>
                    <testsuite name="example.spec.ts">
                        <testcase
                            name="test1" time="0.123"
                            classname="example.spec.ts"
                        />
                        <testcase
                            name="test2" time="0.456"
                            classname="example.spec.ts"
                        >
                            <failure message="Assertion failed"/>
                        </testcase>
                    </testsuite>
                </testsuites>"""
            )

        # Process the retro
        process_retro(self.retro)

        # Check if the playwright.csv file was created
        playwright_csv_path = self.retro.get_playwright_csv_path(commit_hash)
        self.assertTrue(os.path.exists(playwright_csv_path))

        # Check the content of the playwright.csv file
        with open(playwright_csv_path, newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(
                header,
                [
                    "Commit",
                    "Test Type",
                    "Test Name",
                    "Result",
                    "Duration",
                    "Media Path",
                ],
            )
            row1 = next(reader)
            self.assertEqual(
                row1,
                [
                    commit_hash,
                    "playwright",
                    "example.spec.ts::test1",
                    "passed",
                    "0.123",
                    "",
                ],
            )
            row2 = next(reader)
            self.assertEqual(
                row2,
                [
                    commit_hash,
                    "playwright",
                    "example.spec.ts::test2",
                    "failed",
                    "0.456",
                    "",
                ],
            )
            with self.assertRaises(StopIteration):
                next(reader)  # Check no more rows

    def test_process_retro_vitest(self):
        # Create a sample vitest.xml file
        commit_hash = "test_commit"
        commit_dir = os.path.join(self.retro.get_test_output_dir(commit_hash))
        os.makedirs(commit_dir, exist_ok=True)  # Only create commit dir

        vitest_xml_path = os.path.join(commit_dir, "vitest.xml")
        with open(vitest_xml_path, "w") as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
                <testsuites>
                  <testsuite name="example.test.ts">
                    <testcase name="testA" time="0.200"
                        file="example.test.ts" classname="example.test.ts"/>
                    <testcase name="testB" time="0.300"
                        file="example.test.ts" classname="example.test.ts"/>
                  </testsuite>
                </testsuites>"""
            )

        # Process the retro
        process_retro(self.retro)

        # Check if the vitest.csv file was created
        vitest_csv_path = self.retro.get_vitest_csv_path(commit_hash)
        self.assertTrue(os.path.exists(vitest_csv_path))

        # Check the content of the vitest.csv file
        with open(vitest_csv_path, newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(
                header,
                [
                    "Commit",
                    "Test Type",
                    "Test Name",
                    "Result",
                    "Duration",
                    "Media Path",
                ],
            )
            row1 = next(reader)
            self.assertEqual(
                row1,
                [
                    commit_hash,
                    "vitest",
                    "example.test.ts::testA",
                    "passed",
                    "0.200",
                    "",
                ],
            )
            row2 = next(reader)
            self.assertEqual(
                row2,
                [
                    commit_hash,
                    "vitest",
                    "example.test.ts::testB",
                    "passed",
                    "0.300",
                    "",
                ],
            )
            with self.assertRaises(StopIteration):
                next(reader)  # Check no more rows
