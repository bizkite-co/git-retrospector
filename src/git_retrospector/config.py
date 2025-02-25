#!/usr/bin/env python3
import os
from pathlib import Path

from pydantic import BaseModel, DirectoryPath, model_validator


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

    def print_full_paths(self):
        """Prints the full paths of repo_under_test_path and test_result_dir."""
        # print(f"Repository Under Test Path: {self.repo_under_test_path}")
        # print(f"Test Result Directory: {self.test_result_dir}")
