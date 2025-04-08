#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import subprocess

from pydantic import BaseModel, DirectoryPath, model_validator, Field
import toml
import logging


class TestRunner(BaseModel):
    name: str
    command: str
    output_dir: str


class Retro(BaseModel):  # Renamed class
    """
    Configuration settings for git-retrospector.
    """

    name: str
    remote_repo_path: DirectoryPath  # Renamed
    github_remote: str = ""
    github_repo_name: str = ""
    github_repo_owner: str = ""
    github_project_name: str = ""
    github_project_number: int = 0
    github_project_owner: str = ""
    test_result_dir: str = ""
    test_runners: list[TestRunner] = []
    test_output_dir: str = "test-output"
    # Initialize as empty, will be set in __init__
    local_test_output_dir_full: str = Field(default="", exclude=True)
    local_cwd: str = Field(default="", exclude=True)  # Also exclude local_cwd

    def __init__(self, *, name: str, **data):  # Renamed
        captured_cwd = os.getcwd()
        super().__init__(name=name, **data)
        self.local_cwd = captured_cwd
        self.local_test_output_dir_full = str(
            Path(self.local_cwd) / "retros" / self.name / self.test_output_dir
        )
        logging.info(
            f"""Retro init complete: name={self.name}, """
            f"""remote_repo_path={self.remote_repo_path}, """
            f"""local_cwd={self.local_cwd}, """
            f"""local_test_output_dir_full={self.local_test_output_dir_full}"""
        )
        config_file_path = self.get_config_file_path()
        if os.path.exists(config_file_path):
            with open(config_file_path) as config_file:
                config_data = toml.load(config_file)
                for key, value in config_data.items():
                    if key == "test_runners":
                        self.test_runners = [TestRunner(**tr) for tr in value]
                    elif hasattr(self, key) and key not in [
                        "local_test_output_dir_full",
                        "local_cwd",
                    ]:
                        setattr(self, key, value)
        else:
            os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
            config_data = self.model_dump(
                exclude={"local_test_output_dir_full", "local_cwd"}
            )
            with open(config_file_path, "w") as config_file:
                toml.dump(config_data, config_file)

    def get_retro_dir(self):
        return Path(self.local_cwd) / "retros" / self.name

    @model_validator(mode="before")
    def create_and_resolve_paths(cls, values):
        logging.info(f"create_and_resolve_paths: values={values}")
        if "name" not in values:
            raise ValueError("`name` must be provided")
        if "test_output_dir" not in values:
            values["test_output_dir"] = "test-output"
        if "remote_repo_path" in values:
            values["remote_repo_path"] = str(Path(values["remote_repo_path"]).resolve())
        else:
            logging.warning("remote_repo_path missing during validation")
        logging.info(f"create_and_resolve_paths: returning values={values}")
        return values

    @staticmethod
    def is_test_environment():
        return os.environ.get("TEST_ENVIRONMENT") is not None

    @staticmethod
    def remove_retro_dir(retro_name):
        retro_dir = Path("retros") / retro_name
        if retro_dir.exists():
            shutil.rmtree(retro_dir)

    def get_test_output_dir(self, commit_hash=None):
        base_path = Path(self.local_test_output_dir_full)
        if commit_hash:
            return base_path / commit_hash
        return base_path

    def get_tool_summary_dir(self, commit_hash):
        return self.get_test_output_dir(commit_hash) / "tool-summary"

    def get_playwright_xml_path(self, commit_hash):
        return self.get_test_output_dir(commit_hash) / "playwright.xml"

    def get_vitest_log_path(self, commit_hash):
        return self.get_test_output_dir(commit_hash) / "vitest.log"

    def get_vitest_xml_path(self, commit_hash):
        return self.get_test_output_dir(commit_hash) / "vitest.xml"

    def get_playwright_csv_path(self, commit_hash):
        return self.get_tool_summary_dir(commit_hash) / "playwright.csv"

    def get_vitest_csv_path(self, commit_hash):
        return self.get_tool_summary_dir(commit_hash) / "vitest.csv"

    def create_output_dirs(self, commit_hash=None):
        if commit_hash:
            self.get_test_output_dir(commit_hash).mkdir(parents=True, exist_ok=True)
            self.get_tool_summary_dir(commit_hash).mkdir(parents=True, exist_ok=True)
        else:
            self.get_test_output_dir().mkdir(parents=True, exist_ok=True)

    def remove_output_dirs(self, commit_hash=None):
        dir_to_remove = self.get_test_output_dir(commit_hash)
        if dir_to_remove.exists():
            shutil.rmtree(dir_to_remove, ignore_errors=True)

    def path_exists(self, relative_path):
        full_path = self.get_retro_dir() / relative_path
        return full_path.exists()

    def is_dir(self, relative_path):
        full_path = Path(relative_path)
        if full_path.is_absolute() and full_path.exists():
            return full_path.is_dir()
        full_path = self.get_retro_dir() / relative_path
        return full_path.is_dir()

    def list_commit_dirs(self):
        commit_dirs = []
        base_output_dir = self.get_test_output_dir()
        if base_output_dir.exists():
            for item in base_output_dir.iterdir():
                if item.is_dir():
                    commit_dirs.append(item)
        return commit_dirs

    def get_commits_log_path(self):
        return self.get_retro_dir() / "commits.log"

    def get_config_file_path(self):
        return self.get_retro_dir() / "retro.toml"

    def move_test_results_to_local(
        self, commit_hash, output_path, output_filename=None
    ):
        """
        Moves test results from the remote repository to the local repository.
        """
        remote = self.remote_repo_path / Path(output_path)
        local_base = Path(self.local_test_output_dir_full) / commit_hash
        local = local_base / (
            output_filename if output_filename else Path(output_path).name
        )

        # --- Logging Added ---
        logging.info("Attempting to move test results:")
        logging.info(f"  Source (remote): {remote} (exists: {remote.exists()})")
        logging.info(f"  Destination (local): {local}")
        # --- End Logging ---

        if remote.exists():
            try:
                local.parent.mkdir(parents=True, exist_ok=True)
                logging.info(f" Ensured local parent directory exists: {local.parent}")

                if remote.is_dir():
                    logging.info(" Source is directory. Copying tree...")
                    shutil.copytree(str(remote), str(local), dirs_exist_ok=True)
                    logging.info(
                        f" Copytree finished. Removing remote directory: {str(remote)}"
                    )
                    shutil.rmtree(str(remote))
                else:
                    logging.info(" Source is file. Copying file...")
                    shutil.copy2(str(remote), str(local))
                    logging.info(
                        f" Copy2 finished. Removing remote file: {str(remote)}"
                    )
                    os.remove(str(remote))
                logging.info(
                    "Successfully moved test results from %s to %s",
                    remote,
                    local,
                )
            except Exception as e:
                logging.error(
                    "Error during move operation: %s, %s, %s",
                    remote,
                    local,
                    e,
                    exc_info=True,  # Log traceback
                )
        else:
            logging.warning(f"Source path {remote} does not exist. Skipping move.")

    def rename_file(self, old_path, new_name):
        old_path_obj = Path(old_path)
        if not old_path_obj.is_absolute():
            old_path_obj = self.get_retro_dir() / old_path_obj

        if old_path_obj.exists():
            new_path = old_path_obj.parent / new_name
            old_path_obj.rename(new_path)
        else:
            logging.warning(f"Cannot rename, path does not exist: {old_path_obj}")

    def change_to_repo_dir(self):
        logging.info(f"Changing CWD to: {self.remote_repo_path}")
        os.chdir(self.remote_repo_path)

    def restore_cwd(self):
        logging.info(f"Restoring CWD to: {self.local_cwd}")
        os.chdir(self.local_cwd)

    def init_repo(self):
        subprocess.run(
            ["git", "init"],
            cwd=self.remote_repo_path,
            check=True,
            capture_output=True,
            text=True,
        )

    def run_tests(self, test_runner, commit_hash):
        command = test_runner.command  # Changed to dot notation
        logging.info(f"Test runner name: {test_runner.name}")  # Changed to dot notation
        log_file_path = (
            self.get_test_output_dir(commit_hash) / f"{test_runner.name}.log"
        )  # Changed to dot notation
        logging.info(f"Initial log_file_path: {log_file_path}")

        result = None
        e_info = None

        try:
            logging.info(f"Running tests with command: {command}")
            self.change_to_repo_dir()
            logging.info(
                f"Current working directory after change_to_repo_dir: {os.getcwd()}"
            )
            logging.info(f"log_file_path after cwd change: {log_file_path}")

            result = subprocess.run(
                command,
                shell=True,
                text=True,
                cwd=self.remote_repo_path,
                capture_output=True,
            )
            if result.returncode != 0:
                logging.warning(
                    f"""Test runner '{
                        test_runner.name # Changed to dot notation
                        }' returned non-zero exit code: {
                        result.returncode
                    }"""
                )

        except Exception as e:
            logging.error(f"Error running tests: {e}")
            e_info = e
            stdout = getattr(e, "stdout", "N/A")
            stderr = getattr(e, "stderr", "N/A")
            logging.error(f"stdout: {stdout}")
            logging.error(f"stderr: {stderr}")

        finally:
            logging.info(f"Entering finally block. log_file_path: {log_file_path}")
            try:
                log_file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(log_file_path, "w") as log_file:
                    logging.info(f"Opened log file for writing: {log_file_path}")
                    if result:
                        log_file.write(f"STDOUT:\n{result.stdout}\n")
                        log_file.write(f"STDERR:\n{result.stderr}\n")
                        log_file.write(f"RETURN CODE: {result.returncode}\n")
                        logging.info("Wrote result to log file.")
                    elif e_info:
                        log_file.write(f"EXCEPTION: {e_info}\n")
                        stdout = getattr(e_info, "stdout", "N/A")
                        stderr = getattr(e_info, "stderr", "N/A")
                        log_file.write(f"STDOUT (from exception):\n{stdout}\n")
                        log_file.write(f"STDERR (from exception):\n{stderr}\n")
                        logging.info("Wrote exception info to log file.")
                    else:
                        log_file.write("No result or exception captured.\n")
                        logging.warning("No result or exception to write to log file.")

                    log_file.flush()
                    logging.info("Flushed log file.")
            except Exception as log_e:
                logging.error(f"Could not write to log file {log_file_path}: {log_e}")
            self.restore_cwd()
            logging.info(f"Current working directory after restore_cwd: {os.getcwd()}")

    @staticmethod
    def initialize(
        target_name,
        remote_repo_path,
        project_root,
        github_remote="",
        github_repo_name="",
        github_repo_owner="",
        github_project_name="",
        github_project_number=0,
        github_project_owner="",
        test_result_dir="",
        test_runners=None,
    ):
        logging.info(
            f"""Initializing retro with: target_name={target_name}, """
            f"""remote_repo_path={remote_repo_path}, project_root={project_root}"""
        )

        retro_dir = Path(project_root) / "retros" / target_name
        config_file_path = retro_dir / "retro.toml"

        logging.info(f"Retro dir: {retro_dir}")
        logging.info(f"Config file path: {config_file_path}")

        if config_file_path.exists():
            logging.info(f"Retro already exists for {target_name}")
            return

        retro_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {retro_dir}")

        if not Path(remote_repo_path).is_dir():
            raise ValueError(f"Invalid target repository path: {remote_repo_path}")

        try:
            retro = Retro(
                name=target_name,
                remote_repo_path=remote_repo_path,
                github_remote=github_remote,
                github_repo_name=github_repo_name,
                github_repo_owner=github_repo_owner,
                github_project_name=github_project_name,
                github_project_number=github_project_number,
                github_project_owner=github_project_owner,
                test_result_dir=test_result_dir,
                test_runners=test_runners or [],
            )
        except Exception as e:
            logging.error(f"Error creating Retro instance during initialization: {e}")
            raise

        config_data = retro.model_dump(
            exclude={"local_test_output_dir_full", "local_cwd"}
        )

        with open(config_file_path, "w") as config_file:
            toml.dump(config_data, config_file)
        logging.info(f"Initialized retro for {target_name} at {retro_dir}")
