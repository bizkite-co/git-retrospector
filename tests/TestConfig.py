import unittest
import tempfile
import shutil
from git_retrospector.retro import Retro
import logging
from pathlib import Path


class BaseTest(unittest.TestCase):
    """Base class for tests, providing shared setup."""

    @classmethod
    def setUpClass(cls):
        """Setup that runs once before all tests in the class."""
        cls.temp_dir = tempfile.mkdtemp()

        # Create a test_repo directory in the temp_dir
        test_repo_path = Path(cls.temp_dir) / "test_repo"
        test_repo_path.mkdir(parents=True, exist_ok=True)

        cls.retro = Retro(
            name="test_retro",
            repo_under_test_path=str(test_repo_path),
            output_paths={},
        )
        logging.info(f"Temporary directory: {cls.temp_dir}")

    @classmethod
    def tearDownClass(cls):
        """Cleanup that runs once after all tests in the class."""
        shutil.rmtree(cls.temp_dir)
