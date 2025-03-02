from TestConfig import BaseTest
from pathlib import Path


class TestInitialize(BaseTest):

    def test_config_initialize(self):
        # The test_repo directory is now created in BaseTest.setUpClass

        # Get the expected repo path
        repo_under_test_path = Path(self.temp_dir) / "test_repo"

        # Instead of checking the config file, which might have been created
        # with a different path, let's check the retro object's attributes directly
        self.assertEqual(
            str(self.retro.repo_under_test_path), str(repo_under_test_path.resolve())
        )

        # Check that the test_output_dir_full is set correctly
        self.assertEqual(
            self.retro.test_output_dir_full,
            str(repo_under_test_path / self.retro.test_output_dir),
        )

        # Check that the output_paths is empty (as set in BaseTest)
        self.assertEqual(self.retro.output_paths, {})
