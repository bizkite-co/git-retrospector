# Migration Plan: `git-work-estimator`

This document outlines the plan to migrate the `git-work-estimator` tool into the `git-retrospector` repository.

---

## Tool Overview

The `git-work-estimator` is a Python script that analyzes a git repository's history to produce a client-facing work summary. It goes beyond simple commit counting by using a configurable, dynamic model to estimate work hours and by assembling a detailed, value-focused prompt for an LLM.

### Core Features

1.  **Dynamic Work Hour Estimation:**
    *   **Dynamic Decay Model:** Calculates an `estimated_hours` value by applying a linear decay function to the time gaps between commits.
    *   **Commit-Size Modulation:** The decay rate is dynamically adjusted based on the size (lines changed in code files) of the commit that follows a time gap. Large commits can extend the time window where work is considered to have occurred, providing a more nuanced estimate than a fixed cutoff.

2.  **Commit Statistics Analysis:**
    *   For every commit, the script calculates detailed statistics, including a list of changed files with insertion and deletion counts for each.
    *   It calculates a `code_change_score` based only on changes to code files (e.g., `.ts`, `.py`, `.html`), ignoring documentation and data files.

3.  **Value-Focused, Templated Prompt Generation:**
    *   The script assembles a final prompt (`full_prompt.txt`) from several components, designed to frame the technical work in terms of business value.
    *   **Templates:** It uses hand-editable markdown files for high-level context (`product_summary.md`, `client_profile.md`, `value_propositions.md`).
    *   **Automated Data:** It combines these templates with an automatically generated analysis of the git history (`work_prompt.txt`).

4.  **Automated LLM Summarization:**
    *   The script automatically calls the Gemini API with the assembled prompt.
    *   It saves the generated client-facing summary to a timestamped markdown file in the `responses/` directory.

### File Structure

The tool and its artifacts are organized within the `.git-work-estimate/` directory:

```
.git-work-estimate/
├── Makefile              # Convenience tasks for running analysis.
├── MIGRATION.md          # This file.
├── README.md             # Tool documentation.
├── full_prompt.txt       # The final, assembled prompt sent to the LLM.
├── work_analysis.json    # Raw JSON data of the full analysis.
├── work_prompt.txt       # The auto-generated work analysis part of the prompt.
├── responses/            # Directory for final, timestamped LLM summaries.
│   └── 20251001_client_summary.md
├── src/
│   └── analyze_work.py   # The main Python script.
└── templates/
    ├── client_profile.md   # Editable client description.
    ├── product_summary.md  # Editable product description.
    └── value_propositions.md # Editable summary of value delivered.
```

### Dependencies

*   Python 3.x
*   `curl` must be installed and available in the system's PATH.
*   The `GEMINI_API_KEY` environment variable must be set.

---

## Phase 2: Integration Steps

This section outlines the plan to refactor the script for integration into the `git-retrospector` project.

1.  **Copy Files:** Move the entire `.git-work-estimate` directory into the `git-retrospector` repository, likely under a `contrib/` or `tools/` subdirectory.

2.  **Decouple Paths:** The script has already been refactored to accept a `repo_path` argument, making it portable. The `Makefile` will need to be updated to point to the correct repository path from its new location.

3.  **Integrate as a Module:** For a cleaner integration, the core logic from `analyze_work.py` should be moved into a function or class within the `git_retrospector` source tree (e.g., `src/git_retrospector/work_estimator.py`).

4.  **Create CLI Command:** The new module should be exposed through the main `git-retrospector` CLI, potentially as a new subcommand like `estimate-work`.
