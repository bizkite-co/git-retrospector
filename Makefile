# Makefile for git-retrospector

.PHONY: help install lint retro analyze-work

# Get the absolute path of the current directory
# and export it for use in other commands.
export CWD := $(shell pwd)

help:
	@echo "Available commands:"
	@echo "  install       - Install the project and its dependencies in a virtual environment."
	@echo "  lint          - Run ruff linter."
	@echo "  retro         - Run git-retrospector on a target repository. Usage: make retro repo=/path/to/repo"
	@echo "  analyze-work  - Run the work estimator for a given profile. Usage: make analyze-work profile=turboship"


install:
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
	fi
	@. .venv/bin/activate && pip install -e .
	@echo "Installation complete. Run 'source .venv/bin/activate' to use the virtual environment."

lint:
	@echo "Running ruff linter..."
	@ruff check .

# Example: make retro repo=/path/to/handterm-proj/handterm
retro:
ifndef repo
	$(error repo is not set. Usage: make retro repo=<path_to_repo>)
endif
	@. .venv/bin/activate && python -m git_retrospector.retrospector $(repo)

# Example: make analyze-work profile=turboship
analyze-work:
ifndef profile
	$(error profile is not set. Usage: make analyze-work profile=<profile_name>)
endif
	@. .venv/bin/activate && python tools/work-estimator/src/analyze_work.py $(profile)
