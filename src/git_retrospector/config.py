#!/usr/bin/env python3
import os
from pathlib import Path

from pydantic import BaseModel, DirectoryPath, model_validator
import toml


class Config(BaseModel):
    """
    Configuration settings for git-retrospector.
    """

    name: str
    repo_under_test_path: DirectoryPath
    test_result_dir: DirectoryPath
    output_paths: dict
    test_output_dir: str = "test-output"

    @model_validator(mode="before")
    def create_and_resolve_paths(cls, values):
        if "name" not in values:
            raise ValueError("`name` must be provided")

        if "test_result_dir" not in values:
            if "test_output_dir" not in values:
                values["test_output_dir"] = "test-output"
            values["test_result_dir"] = os.path.join(
                "retros", values["name"], values["test_output_dir"]
            )

        # Resolve paths to absolute paths
        if "repo_under_test_path" in values:
            values["repo_under_test_path"] = Path(
                values["repo_under_test_path"]
            ).resolve()
        values["test_result_dir"] = Path(values["test_result_dir"]).resolve()

        # Ensure test_result_dir exists.
        os.makedirs(values["test_result_dir"], exist_ok=True)
        return values

    @staticmethod
    def initialize(target_name, repo_under_test_path, output_base_dir="retros"):
        """
        Initializes the target-specific directory and config file.

        Args:
            target_name (str): The name of the target repository.
            repo_under_test_path (str): The path to the target repository.
            output_base_dir (str, optional): The base directory for retrospectives.
                Defaults to "retros".
        """
        config_file_path = os.path.join(output_base_dir, target_name, "config.toml")
        if not os.path.exists(config_file_path):
            config = Config(
                name=target_name,
                repo_under_test_path=repo_under_test_path,
                test_result_dir=os.path.join(output_base_dir, target_name),
                output_paths={
                    "vitest": "test-output/vitest.xml",
                    "playwright": "test-output/playwright.xml",
                },
            )
            # Convert Path objects to strings for TOML serialization
            config_data = config.model_dump()
            config_data["repo_under_test_path"] = str(
                config_data["repo_under_test_path"]
            )
            config_data["test_result_dir"] = str(config_data["test_result_dir"])

            with open(config_file_path, "w") as config_file:
                toml.dump(config_data, config_file)  # Use config_data
        return config_file_path

    def print_full_paths(self):
        """Prints the full paths of repo_under_test_path and test_result_dir."""
        # print(f"Repository Under Test Path: {self.repo_under_test_path}")
        # print(f"Test Result Directory: {self.test_result_dir}")
