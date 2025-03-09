#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import subprocess

from pydantic import BaseModel, DirectoryPath, model_validator, Field
import toml
import logging
import time


class Retro(BaseModel):  # Renamed class
    """
    Configuration settings for git-retrospector.
    """

    name: str
    remote_repo_path: DirectoryPath  # Renamed
    # test_result_dir: str  # Removed
    # output_paths: dict # Removed
    test_output_dir: str = "test-output"
    local_test_output_dir_full: str = Field(default="", exclude=True)
    local_cwd: str = ""  # Renamed
    test_result_dir: str = ""
    test_runners: list[dict] = Field(default=[], exclude=True)

    def __init__(self, *, name: str, remote_repo_path: str, **data):  # Renamed
        # Initialize Pydantic model first
        super().__init__(
            name=name,
            remote_repo_path=remote_repo_path,  # Renamed
            # output_paths=output_paths, # Removed
            **data,
        )
        logging.info(
            f"""Retro init: name={
                self.name
            }, remote_repo_path={self.remote_repo_path}"""  # Renamed
        )

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

        # Set the local_test_output_dir_full attribute
        self.local_cwd = (
            os.getcwd()
        )  # Store original CWD and set before local_test_output_dir_full # Renamed
        self.local_test_output_dir_full = str(
            Path(self.local_cwd)
            / "retros"
            / self.name
            / self.test_output_dir  # Modified
        )

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
        values["remote_repo_path"] = str(  # Renamed
            Path(values["remote_repo_path"]).resolve()  # Renamed and corrected
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
        commit_hash_dir = os.path.join(self.get_test_output_dir(commit_hash))
        tool_summary_dir = os.path.join(commit_hash_dir, "tool-summary")
        logging.info(f"create_commit_hash_dir: commit_hash_dir = {commit_hash_dir}")
        os.makedirs(commit_hash_dir, exist_ok=True)
        os.makedirs(tool_summary_dir, exist_ok=True)
        # Explicitly check and wait for directory creation
        timeout = 5  # seconds
        start_time = time.time()
        while (
            not os.path.exists(commit_hash_dir) and time.time() - start_time < timeout
        ):
            time.sleep(0.1)
        if not os.path.exists(commit_hash_dir):
            logging.error(
                f"Commit hash directory did not get created: {commit_hash_dir}"
            )
        while (
            not os.path.exists(tool_summary_dir) and time.time() - start_time < timeout
        ):
            time.sleep(0.1)
        if not os.path.exists(tool_summary_dir):
            logging.error(
                f"Tool summary directory did not get created: {tool_summary_dir}"
            )

        logging.info(f"commit_hash_dir exists: {os.path.exists(commit_hash_dir)}")
        logging.info(f"tool_summary_dir exists: {os.path.exists(tool_summary_dir)}")
        return commit_hash_dir, tool_summary_dir

    @staticmethod
    def remove_commit_hash_dir(retro_name, commit_hash):
        commit_hash_dir, _ = Retro.get_commit_hash_dir(retro_name, commit_hash)
        shutil.rmtree(commit_hash_dir, ignore_errors=True)

    def print_full_paths(self):
        """Prints the full paths of remote_repo_path and test_output_dir."""
        # print(f"Repository Under Test Path: {self.remote_repo_path}") # Renamed
        # print(f"Test Output Directory: {self.local_test_output_dir_full}")
        pass

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

    def get_vitest_xml_path(self, commit_hash):
        """Returns the path to the vitest.xml file for a specific commit."""
        return Path(self.get_test_output_dir(commit_hash)) / "vitest.xml"

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

    def move_test_results_to_local(
        self, commit_hash, output_path, output_filename=None
    ):
        """
        Moves test results from the remote repository to the local repository.

        Args:
            commit_hash (str): The hash of the commit.
            output_path (str | Path): The path to the
            output *file or directory* in the remote repository.
            output_filename (str, optional): The new name of the file in
            the local repository. Defaults to None.
        """
        remote = self.remote_repo_path / output_path  # Expected location in remote repo
        local = Path(self.local_test_output_dir_full) / commit_hash  # Local destination
        if output_filename:
            local = local / output_filename

        logging.info(f"Moving test results from {remote} to {local}")
        logging.info(f"Remote exists: {remote.exists()}")  # Added logging

        if remote.exists():
            try:
                if remote.is_dir():
                    shutil.copytree(str(remote), str(local), dirs_exist_ok=True)
                    logging.info(f"Removing remote directory: {str(remote)}")
                    shutil.rmtree(str(remote))  # Remove source after copy
                else:
                    # Ensure the parent directory exists
                    local.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(remote), str(local))  # Copy a single file
                    os.remove(str(remote))
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
            logging.warning(f"Source path {remote} does not exist. Skipping copy.")

    def rename_file(self, old_path, new_name):
        new_path = Path(old_path).parent / new_name
        Path(old_path).rename(new_path)

    def change_to_repo_dir(self):
        """Changes the current working directory to the target repo."""
        logging.info(f"Changing CWD to: {self.remote_repo_path}")  # Renamed
        os.chdir(self.remote_repo_path)  # Renamed

    def restore_cwd(self):
        """Restores the current working directory to the original value."""
        logging.info(f"Restoring CWD to: {self.local_cwd}")  # Renamed
        os.chdir(self.local_cwd)  # Renamed

    def init_repo(self):
        """Initializes a git repository in the remote_repo_path."""
        subprocess.run(
            ["git", "init"],
            cwd=self.remote_repo_path,  # Renamed
            check=True,
            capture_output=True,
            text=True,
        )

    def run_tests(self, test_runner, commit_hash):
        """
        Runs tests for a specific commit using the specified test runner.

        Args:
            test_runner (dict): A dictionary containing the test runner configuration
                (e.g., name, command, output_dir).
            commit_hash (str): The hash of the commit to run tests against.

        **IMPORTANT: We intentionally DO NOT use check=True in the subprocess.run().**
        This is because the test runners themselves (e.g., vitest, playwright) might
        return a non-zero exit code if tests fail.  We *expect* this to happen, and
        we want to capture the output (stdout and stderr) even when tests fail.
        Raising an exception here would prevent us from capturing the output and
        moving the test results, and would halt the retrospector process prematurely.
        We handle non-zero exit codes by logging a warning, but we *do not* treat
        them as fatal errors within the retrospector. The errors are in the *target*
        repository's tests, not in the retrospector itself.
        """
        command = test_runner["command"]
        # Create a log file path for this specific test run
        logging.info(f"Test runner name: {test_runner['name']}")
        log_file_path = (
            Path(self.local_test_output_dir_full)
            / commit_hash
            / f"{test_runner['name']}.log"
        )
        logging.info(f"Initial log_file_path: {log_file_path}")

        try:
            logging.info(f"Running tests with command: {command}")
            self.change_to_repo_dir()
            logging.info(
                f"Current working directory after change_to_repo_dir: {os.getcwd()}"
            )
            logging.info(f"log_file_path after cwd change: {log_file_path}")

            # Capture both stdout and stderr
            result = subprocess.run(
                command,
                shell=True,
                text=True,
                cwd=self.remote_repo_path,
                capture_output=True,  # Capture the output
            )
            # Check the return code and log a warning if it's non-zero
            if result.returncode != 0:
                logging.warning(
                    f"""Test runner '{
                        test_runner['name']
                        }' returned non-zero exit code: {
                        result.returncode
                    }"""
                )

        except Exception as e:
            logging.error(f"Error running tests: {e}")
            logging.error(f"stdout: {e.stdout}")
            logging.error(f"stderr: {e.stderr}")
            raise e  # Re-raise the exception
        finally:
            # Always write the log file, regardless of success or failure
            logging.info(f"Entering finally block. log_file_path: {log_file_path}")
            try:
                with open(log_file_path, "w") as log_file:
                    logging.info(f"Opened log file for writing: {log_file_path}")
                    if "result" in locals():
                        log_file.write(f"STDOUT:\n{result.stdout}\n")
                        log_file.write(f"STDERR:\n{result.stderr}\n")
                        log_file.write(f"RETURN CODE: {result.returncode}\n")
                        logging.info("Wrote result to log file.")
                    elif "e" in locals():
                        log_file.write(f"STDOUT:\n{locals().e.stdout}\n")
                        log_file.write(f"STDERR:\n{locals().e.stderr}\n")
                        logging.info("Wrote exception to log file.")
                    log_file.flush()
                    logging.info("Flushed log file.")
            except Exception as e:
                logging.error(f"Could not write to log file {log_file_path}: {e}")
            self.restore_cwd()
            logging.info(f"Current working directory after restore_cwd: {os.getcwd()}")

    @staticmethod
    def initialize(
        target_name, remote_repo_path, project_root
    ):  # Modified parameter name
        """
        Initializes a retro for a given target repository.

        Creates a directory structure under 'retros/<target_name>' and
        creates a 'retro.toml' configuration file.

        Args:
            target_name (str): The name of the target.
            remote_repo_path (str): The path to the target repository.
            project_root (str): The absolute path to the project root.

        Raises:
            ValueError: If the target repository path is invalid.
        """
        logging.info(
            f"""Initializing retro with: target_name={
                target_name
            }, remote_repo_path={
                remote_repo_path}, project_root={project_root}"""  # Modified
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
        if not os.path.isdir(remote_repo_path):  # Modified
            raise ValueError(
                f"Invalid target repository path: {remote_repo_path}"
            )  # Modified

        # Create a Retro instance with resolved paths, using the correct key
        retro = Retro(name=target_name, remote_repo_path=remote_repo_path)  # Modified

        # Convert Path objects to strings for TOML serialization
        config_data = retro.model_dump()

        # Write config to file
        with open(config_file_path, "w") as config_file:
            toml.dump(config_data, config_file)
        logging.info(f"Initialized retro for {target_name} at {retro_dir}")
