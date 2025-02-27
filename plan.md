# Plan to Address Issue #15 (Install Click or other CLI lib)

## Overview

This plan outlines the steps to integrate a CLI library (Click) and an interactive prompt library (python-prompt-toolkit) into the `git-retrospector` project. This will improve the user experience and provide a more structured way to interact with the tool.

## Steps

1.  **Install Libraries:**
    *   Add `click` and `python-prompt-toolkit` as project dependencies.
    *   Use `pip install click prompt-toolkit` to install the libraries (using `uv` as specified in `.clinerules`).

2.  **Refactor Existing Code:**
    *   Identify the current entry point of the application (likely in `retrospector.py` or a dedicated `runners.py` file).
    *   Modify the code to use `click` for defining commands and options. This will involve:
        *   Using `@click.command()` to decorate main functions.
        *   Using `@click.option()` to define command-line options.
        *   Using `@click.argument()` to define command-line arguments.

3.  **Implement Interactive Prompts:**
    *   Use `python-prompt-toolkit` where interactive input is needed. Examples include:
        *   Selecting options from a list.
        *   Confirming actions (yes/no prompts).
        *   Providing input with autocompletion.
    * Add a prompt for the available options for when the user executes the command without parameters.
      * Check the status of the retro config, if a retro name is passed in without additional parameters, and notify the user of the status of the config.

4.  **Create Unit Tests:**
    *   Write unit tests for the new CLI functionality.
    *   Ensure proper argument parsing and interactive behavior are tested.
    *   Use the `unittest` framework, as specified in `.clinerules`.

5.  **Switch to Code Mode:**
    * After the plan is approved, switch to Code mode to implement these changes.
