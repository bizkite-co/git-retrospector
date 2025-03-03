#!/usr/bin/env python3
# import subprocess # No longer needed
# import os # No longer needed
# import logging # No longer needed


def run_vitest(target_repo, output_dir, retro):
    """Runs vitest tests and captures output."""
    retro.run_tests("vitest", output_dir)


def run_playwright(target_repo, output_dir, retro):
    """Runs playwright tests and captures output."""
    retro.run_tests("playwright", output_dir)
