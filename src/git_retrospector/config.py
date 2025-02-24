#!/usr/bin/env python3
import os
from pydantic import BaseModel, DirectoryPath, model_validator

class Config(BaseModel):
    """
    Configuration settings for git-retrospector.
    """
    name: str
    target_repo_path: DirectoryPath
    test_result_dir: DirectoryPath
    output_paths: dict
    test_output_dir: str = "test-output"

    @model_validator(mode='before')
    def create_test_result_dir_if_needed(cls, values):
        if "test_result_dir" not in values:
            if "name" not in values:
                raise ValueError("`name` must be provided to create `test_result_dir`")
            if "test_output_dir" not in values:
                values["test_output_dir"] = "test-output"
            values["test_result_dir"] = os.path.join("retros", values["name"], values["test_output_dir"])

        # Ensure test_result_dir exists. No need to check if values['test_result_dir'] is a directory here.
        # Pydantic will do it.
        os.makedirs(values["test_result_dir"], exist_ok=True)
        return values
