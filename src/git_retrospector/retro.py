#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import subprocess

from pydantic import BaseModel, DirectoryPath, model_validator, Field
import toml
import logging


class Retro(BaseModel):  # Renamed class
    """
    Configuration settings for git-retrospector.
    """

    name: str
    repo_under_test_path: DirectoryPath
    # test_result_dir: str  # Removed
    # output_paths: dict # Removed
    test_output_dir: str = "test-output"
    local_test_output_dir_full: str = Field(default="", exclude=True)
    original_cwd: str = ""
    test_result_dir: str = ""
    test_runners: list[dict] = Field(default=[], exclude=True)

    def __init__(self, *, name: str, repo_under_test_path: str, **data):
        # Initialize Pydantic model first
        super().__init__(
            name=name,
            repo_under_test_path=repo_under_test_path,
            # output_paths=output_paths, # Removed
            **data,
        )
        logging.info(
            f"""Retro init: name={
                self.name
            }, repo_under_test_path={self.repo_under_test_path}"""
        )

        # Set the local_test_output_dir_full attribute
        self.local_test_output_dir_full = str(
            Path("retros") / self.name / self.test_output_dir
        )
        self.original_cwd = os.getcwd()  # Store original CWD

        # Determine config file path
        if not Retro.is_test_environment():
            config_file_path = os.path.join("retros", self.name, "retro.toml")

            if not os.path.exists(config_file_path):
                # Create directories if they don't exist
                os.makedirs(os.path.dirname(config_file_path), exist_ok=True)

                # Convert Path objects to strings for TOML serialization
                config_data = self.model_dump()

                # Write config to file
                with open(config_file_path, "w") as config_file:
                    toml.dump(config_data, config_file)

    def get_retro_dir(self):
        return os.path.join("retros", self.name)

    @model_validator(mode="before")
    def create_and_resolve_paths(cls, values):
        logging.info(f"create_and_resolve_paths: values={values}")
        # Ensure 'name' is provided, as it's now required by __init__
        if "name" not in values:
            raise ValueError("`name` must be provided")

        # Always construct test_output_dir if not provided
        if "test_output_dir" not in values:
            values["test_output_dir"] = "test-output"

        # Resolve paths to absolute paths
        values["repo_under_test_path"] = str(
            Path(values["repo_under_test_path"]).resolve()
        )

        # Construct the full path to the test output directory
        # This is used internally by methods that need the absolute path
        values["local_test_output_dir_full"] = str(
            Path("retros") / values["name"] / values["test_output_dir"]
        )

        logging.info(f"create_and_resolve_paths: returning values={values}")
        return values

    @staticmethod
    def is_test_environment():
        return os.environ.get("TEST_ENVIRONMENT") is not None

    @staticmethod
    def remove_retro_dir(retro_name):
        retro_dir = os.path.join("retros", retro_name)
        shutil.rmtree(retro_dir)

    def get_commit_hash_dir(self, commit_hash):
        commit_hash_dir = os.path.join(self.get_test_output_dir(commit_hash))
        tool_summary_dir = os.path.join(commit_hash_dir, "tool-summary")
        return commit_hash_dir, tool_summary_dir

    def create_commit_hash_dir(self, commit_hash):
        commit_hash_dir, tool_summary_dir = self.get_commit_hash_dir(commit_hash)
        os.makedirs(commit_hash_dir, exist_ok=True)
        os.makedirs(tool_summary_dir, exist_ok=True)
        return commit_hash_dir, tool_summary_dir

    @staticmethod
    def remove_commit_hash_dir(retro_name, commit_hash):
        commit_hash_dir, _ = Retro.get_commit_hash_dir(retro_name, commit_hash)
        shutil.rmtree(commit_hash_dir, ignore_errors=True)

    def print_full_paths(self):
        """Prints the full paths of repo_under_test_path and test_output_dir."""
        # print(f"Repository Under Test Path: {self.repo_under_test_path}")
        # print(f"Test Output Directory: {self.local_test_output_dir_full}")

    def get_test_output_dir(self, commit_hash=None):
        """Returns the test output directory path."""
        if commit_hash:
            return Path(self.local_test_output_dir_full) / commit_hash
        return Path(self.local_test_output_dir_full)

    def get_tool_summary_dir(self, commit_hash):
        """Returns the tool summary directory path for a specific commit."""
        return Path(self.get_test_output_dir(commit_hash)) / "tool-summary"

    def get_playwright_xml_path(self, commit_hash):
        """Returns the path to the playwright.xml file for a specific commit."""
        return Path(self.get_test_output_dir(commit_hash)) / "playwright.xml"

    def get_vitest_log_path(self, commit_hash):
        """Returns the path to the vitest.log file for a specific commit."""
        return Path(self.get_test_output_dir(commit_hash)) / "vitest.log"

    def get_playwright_csv_path(self, commit_hash):
        """Returns the path to the playwright.csv file for a specific commit."""
        return Path(self.get_tool_summary_dir(commit_hash)) / "playwright.csv"

    def get_vitest_csv_path(self, commit_hash):
        """Returns the path to the vitest.csv file for a specific commit."""
        return Path(self.get_tool_summary_dir(commit_hash)) / "vitest.csv"

    def create_output_dirs(self, commit_hash=None):
        """Creates the necessary directories for test output."""
        if commit_hash:
            self.get_test_output_dir(commit_hash).mkdir(parents=True, exist_ok=True)
            self.get_tool_summary_dir(commit_hash).mkdir(parents=True, exist_ok=True)
        else:
            self.get_test_output_dir().mkdir(parents=True, exist_ok=True)

    def remove_output_dirs(self, commit_hash=None):
        """Removes the test output directories."""
        if commit_hash:
            shutil.rmtree(self.get_test_output_dir(commit_hash), ignore_errors=True)
        else:
            shutil.rmtree(self.get_test_output_dir(), ignore_errors=True)

    def path_exists(self, relative_path):
        """Checks if a path exists relative to the retro root directory."""
        full_path = Path(relative_path)
        if full_path.exists():
            return True
        full_path = Path("retros") / self.name / relative_path
        return full_path.exists()

    def is_dir(self, relative_path):
        """Checks if a path is a directory, relative to the retro root."""
        full_path = Path(relative_path)
        if full_path.exists():
            return full_path.is_dir()
        full_path = Path("retros") / self.name / relative_path
        return full_path.is_dir()

    def list_commit_dirs(self):
        """Lists the commit directories within the retro's test output directory."""
        commit_dirs = []
        for item in self.get_test_output_dir().iterdir():
            if (self.get_test_output_dir() / item).is_dir():
                commit_dirs.append(item)
        return commit_dirs

    def get_commits_log_path(self):
        """Returns the path to the commits.log file."""
        return Path(self.get_retro_dir()) / "commits.log"

    def get_config_file_path(self):
        """Returns the path to the retro.toml file."""
        return Path(self.get_retro_dir()) / "retro.toml"

    def move_test_results_to_local(self, commit_hash, output_dir):
        """
        Moves test results from the remote repository's test-results directory
        to the local repository's test-output directory, organized by commit hash.
        """
        remote = (
            self.repo_under_test_path / output_dir
        )  # Expected location in remote repo
        local = (
            Path(self.get_retro_dir()) / "test-output" / commit_hash
        )  # Local destination
        logging.info(f"Moving test results from {remote} to {local}")
        logging.info(f"Remote exists: {remote.exists()}")  # Added logging
        logging.info(f"Remote contents: {list(remote.glob('*'))}")
        # TODO: Clear the local hash only at creation
        # if local.exists():
        #     logging.info(f"Removing existing destination directory: {local}")
        #     shutil.rmtree(local)
        if remote.exists():  # Only copy if the source exists
            try:
                shutil.copytree(str(remote), str(local), dirs_exist_ok=True)
                logging.info(f"Local contents after copy: {list(local.glob('*'))}")
                shutil.rmtree(str(remote))  # Remove source after copy
                logging.info(
                    f"Local contents after rmtree of remote: {list(local.glob('*'))}"
                )  # NEW LOG LINE
                logging.info(
                    "Successfully moved test results from %s to %s",
                    remote,
                    local,
                )
            except Exception as e:
                logging.error(
                    "Error moving test results: %s, %s, %s",
                    remote,
                    local,
                    e,
                )
        else:
            logging.warning(f"Source directory {remote} does not exist. Skipping copy.")

    def rename_file(self, old_path, new_name):
        new_path = Path(old_path).parent / new_name
        Path(old_path).rename(new_path)

    def change_to_repo_dir(self):
        """Changes the current working directory to the target repo."""
        logging.info(f"Changing CWD to: {self.repo_under_test_path}")
        os.chdir(self.repo_under_test_path)

    def restore_cwd(self):
        """Restores the current working directory to the original value."""
        logging.info(f"Restoring CWD to: {self.original_cwd}")
        os.chdir(self.original_cwd)

    def init_repo(self):
        """Initializes a git repository in the repo_under_test_path."""
        subprocess.run(
            ["git", "init"],
            cwd=self.repo_under_test_path,
            check=True,
            capture_output=True,
            text=True,
        )

    def run_tests(self, test_runner, commit_hash):
        command = test_runner["command"]
        try:
            logging.info(f"Running tests with command: {command}")
            self.change_to_repo_dir()
            logging.info(f"Current working directory: {os.getcwd()}")
            subprocess.run(
                command,
                shell=True,
                check=True,
                text=True,
                cwd=self.repo_under_test_path,
            )
        except subprocess.CalledProcessError as e:
            logging.error(f"Error running tests: {e}")
            logging.error(f"stdout: {e.stdout}")
            logging.error(f"stderr: {e.stderr}")
            raise e
        finally:
            self.restore_cwd()

    @staticmethod
    def initialize(target_name, target_repo_path, project_root):
        """
        Initializes a retro for a given target repository.

        Creates a directory structure under 'retros/<target_name>' and
        creates a 'retro.toml' configuration file.

        Args:
            target_name (str): The name of the target.
            target_repo_path (str): The path to the target repository.
            project_root (str): The absolute path to the project root.

        Raises:
            ValueError: If the target repository path is invalid.
        """
        logging.info(
            f"""Initializing retro with: target_name={
                target_name
                }, target_repo_path={
                target_repo_path}, project_root={project_root}"""
        )

        retro_dir = os.path.join(project_root, "retros", target_name)
        config_file_path = os.path.join(retro_dir, "retro.toml")

        logging.info(f"Retro dir: {retro_dir}")
        logging.info(f"Config file path: {config_file_path}")

        if os.path.exists(config_file_path):
            logging.info(f"Retro already exists for {target_name}")
            return

        # Create directories if they don't exist
        os.makedirs(retro_dir, exist_ok=True)
        logging.info(f"Created directory: {retro_dir}")

        # Check if target_repo_path is a valid directory
        if not os.path.isdir(target_repo_path):
            raise ValueError(f"Invalid target repository path: {target_repo_path}")

        # Create a Retro instance with resolved paths
        retro = Retro(name=target_name, repo_under_test_path=target_repo_path)

        # Convert Path objects to strings for TOML serialization
        config_data = retro.model_dump()

        # Write config to file
        with open(config_file_path, "w") as config_file:
            toml.dump(config_data, config_file)
        logging.info(f"Initialized retro for {target_name} at {retro_dir}")
