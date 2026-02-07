# Git Work Estimate Tool

This tool analyzes the git history of a repository to provide an estimation of work patterns and generate summaries of work done over a given period.

## How it Works

The core of the tool is the `src/analyze_work.py` script. It fetches all git commits within a specified number of days and performs analysis.

### Hour Estimation Model (Dynamic Linear Decay)

The main feature is its dynamic hour estimation model. It assumes that the amount of productive work in a time gap between commits decreases as the gap gets longer, but it adjusts this decay based on the magnitude of the subsequent commit.

1.  **Code Change Score**: For each commit, the script calculates a score by summing the insertions and deletions for code files only (e.g., `.ts`, `.js`, `.py`, etc.), ignoring documentation and data files.

2.  **Dynamic Decay**: This score is then used to add `bonus hours` to the `zero_credit` threshold for the preceding time gap. A commit with a large code change can extend the time window where work is considered to have occurred.
    *   **Baseline (`change_baseline`):** A code change score below this (default: 100) provides no bonus.
    *   **Max Score (`change_max_score`):** A score above this (default: 500) provides the maximum bonus.
    *   **Max Bonus (`max_bonus`):** The maximum number of hours that can be added (default: 5).

This creates a more dynamic and potentially more accurate estimate of work hours.

### Session Grouping

For readability, commits are also grouped into "work sessions". A session is a series of commits where the time between each is less than the `session_gap` (default: 1 hour). This is for reporting only and does not affect the hour estimation.

### Diff Tracking

The script also inspects changes to specific files (`plan.md`, `task.md`) to provide more context on the work being done.

## How to Use

A `Makefile` is provided for convenience. From within the `.git-work-estimate` directory, you can run:

- **`make analyze`**: Runs the analysis with default parameters.
- You can override parameters: `make analyze days=7 zero_credit=8`
- **`make clean`**: Removes the generated analysis files.

## Generated Files

- `work_analysis.json`: The raw JSON output containing all commits, session data, and analysis parameters.
- `llm_prompt.txt`: A text file with a generated prompt for an LLM to produce a qualitative summary of the work.
