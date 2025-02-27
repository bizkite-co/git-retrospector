import unittest
import os
import subprocess
import tempfile

from git_retrospector.retrospector import get_current_commit_hash


class TestProcessCommit(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        subprocess.run(
            ["git", "init"],
            cwd=self.temp_dir.name,
            check=True,
            capture_output=True,
        )
        # Create an empty initial commit
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Initial empty commit"],
            cwd=self.temp_dir.name,
            check=True,
            capture_output=True,
        )
        self.repo_path = self.temp_dir.name
        self.commit_hash = get_current_commit_hash(self.repo_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_process_commit(self):

        # Create a test repo
        test_repo = os.path.join(self.temp_dir.name, "test_repo")
        os.makedirs(test_repo)
        subprocess.run(
            ["git", "init"],
            cwd=test_repo,
            check=True,
            capture_output=True,
        )

        # Create a package.json file
        package_json_path = os.path.join(test_repo, "package.json")
        with open(package_json_path, "w") as f:
            f.write(
                """{
  "name": "test-repo",
  "version": "1.0.0",
  "description": "",
  "main": "index.js",
  "scripts": {
    "test": "echo \\"Error: no test specified\\" && exit 1"
  },
  "keywords": [],
  "author": "",
  "license": "ISC"
}
"""
            )

        # Install Playwright
        # Adding a comment to force a file change
        subprocess.run(
            ["npm", "install", "@playwright/test"],
            cwd=test_repo,
            check=True,
            capture_output=True,
        )

        # Add a file and commit it
        with open(os.path.join(test_repo, "file1.txt"), "w") as f:
            f.write("Initial commit")
        subprocess.run(
            ["git", "add", "."], cwd=test_repo, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=test_repo,
            check=True,
            capture_output=True,
        )

        # Add Playwright setup
        playwright_config_path = os.path.join(test_repo, "playwright.config.ts")
        # Use a fixed output directory for debugging
        playwright_xml_output_path = os.path.abspath("test-output-debug/playwright.xml")

        with open(playwright_config_path, "w") as f:
            f.write(
                f"""import {{ defineConfig }} from '@playwright/test';

export default defineConfig({{
  testDir: './tests',
  reporter: [['junit', {{ outputFile: '{playwright_xml_output_path}' }}]],
}});
"""
            )

        tests_dir = os.path.join(test_repo, "tests")
        os.makedirs(tests_dir)
        example_spec_path = os.path.join(tests_dir, "example.spec.ts")
        with open(example_spec_path, "w") as f:
            f.write(
                """import { test, expect } from '@playwright/test';

test('basic test', () => {
  expect(true).toBe(true);
});
"""
            )

        # Check if Playwright is installed
        subprocess.run(["npx", "playwright", "--version"], cwd=test_repo, check=True)

        # Run Playwright directly
        subprocess.run(["npx", "playwright", "test"], cwd=test_repo, check=True)

        # Check for the existence of playwright.xml in the fixed output directory
        self.assertTrue(os.path.exists(playwright_xml_output_path))
