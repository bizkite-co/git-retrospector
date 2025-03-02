import subprocess
import os
from pathlib import Path
from TestConfig import BaseTest
from git_retrospector.commit_processor import process_commit
import logging


class TestProcessCommit(BaseTest):
    def setUp(self):
        # Initialize a git repository
        subprocess.run(
            ["git", "init"], cwd=self.temp_dir, check=True, capture_output=True
        )
        # Create an empty initial commit
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Initial empty commit"],
            cwd=self.temp_dir,
            check=True,
            capture_output=True,
        )
        # Get the actual commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.temp_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        self.commit_hash = result.stdout.strip()
        logging.info(f"Commit hash: {self.commit_hash}")

        # Create a package.json file
        package_json_path = os.path.join(self.temp_dir, "package.json")
        logging.info(f"package_json_path: {package_json_path}")
        with open(package_json_path, "w") as f:
            f.write(
                """{
  "name": "test-repo",
  "version": "1.0.0",
  "description": "",
  "main": "index.js",
  "scripts": {
    "test": "vitest"
  },
  "keywords": [],
  "author": "",
  "license": "ISC"
}
"""
                + "\n"
            )
        logging.info("package.json exists: " f"{os.path.exists(package_json_path)}")

        # Install Playwright
        # Adding a comment to force a file change
        subprocess.run(
            ["npm", "install", "@playwright/test"],
            cwd=self.temp_dir,
            check=True,
            capture_output=True,
        )

        # Check if node_modules exists
        node_modules_path = Path(self.temp_dir) / "node_modules"
        logging.info(
            "node_modules exists after npm install: " f"{node_modules_path.exists()}"
        )
        self.assertTrue(
            node_modules_path.exists(),
            "node_modules not found at:\n" + str(node_modules_path),
        )

        # Add package.json and commit it
        subprocess.run(
            ["git", "add", "package.json"],
            cwd=self.temp_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Add package.json"],
            cwd=self.temp_dir,
            check=True,
            capture_output=True,
        )

        # Add a file and commit it.  REMOVED - doing this in one commit now.
        # with open(os.path.join(self.temp_dir, "file1.txt"), "w") as f:
        #     f.write("Initial commit")
        # subprocess.run(
        #     ["git", "add", "."], cwd=self.temp_dir, check=True, capture_output=True
        # )
        # subprocess.run(
        #     ["git", "commit", "-m", "Initial commit"],
        #     cwd=self.temp_dir,
        #     check=True,
        #     capture_output=True,
        # )

        # Add Playwright setup
        playwright_config_path = os.path.join(self.temp_dir, "playwright.retro.ts")
        with open(playwright_config_path, "w") as f:
            f.write(
                f"""import {{ defineConfig }} from '@playwright/test';

export default defineConfig({{
testDir: './tests',
reporter: [
    [
        'junit',
        {{ outputFile: '{self.retro.get_playwright_xml_path(self.commit_hash)}' }}
    ]
],
}});
"""
            )

        # Add Vitest setup
        vitest_config_path = os.path.join(self.temp_dir, "vitest.config.ts")
        with open(vitest_config_path, "w") as f:
            f.write(
                f"""import {{ defineConfig }} from 'vitest/config';

export default defineConfig({{
test: {{
  reporters: ['junit'],
  outputFile: '{self.retro.get_vitest_log_path(self.commit_hash)}',
}},
}});
"""
            )

        (Path(self.temp_dir) / "tests").mkdir()
        example_spec_path = Path(self.temp_dir) / "tests" / "example.spec.ts"
        with open(example_spec_path, "w") as f:
            f.write(
                """import { test, expect } from '@playwright/test';

test('basic test', () => {
expect(true).toBe(true);
});
"""
            )

        # Check if Playwright is installed
        subprocess.run(
            ["npx", "playwright", "--version"],
            cwd=self.temp_dir,
            check=True,
            capture_output=True,
            text=True,
        )

        # Unset TEST_ENVIRONMENT temporarily
        original_env = os.environ.copy()
        if "TEST_ENVIRONMENT" in os.environ:
            del os.environ["TEST_ENVIRONMENT"]

        # Run process_commit
        process_commit(
            self.temp_dir, self.commit_hash, "", "main", self.retro
        )  # Dummy branch name

        # Check for the existence of playwright.xml in the output directory
        self.assertTrue(self.retro.get_playwright_xml_path(self.commit_hash).exists())
        # Check for the existence of vitest.log in the output directory
        self.assertTrue(self.retro.get_vitest_log_path(self.commit_hash).exists())

        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)

    # def tearDown(self):
    #     shutil.rmtree(self.temp_dir)
