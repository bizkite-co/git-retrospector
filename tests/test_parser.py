import unittest
import tempfile
import os
import shutil

from git_retrospector.parser import parse_author_line, parse_commit_line
from git_retrospector.git_retrospector import Retro


class TestParser(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)

        # Initialize a Retro object for testing
        self.retro = Retro(
            name="test_retro", remote_repo_path=self.repo_dir, test_output_dir="."
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
