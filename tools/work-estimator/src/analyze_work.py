import argparse
import subprocess
import json
import os
from datetime import datetime, timedelta


def get_commits(days, repo_path):
    """
    Fetches git commits from the last N days.
    Returns a list of commit dictionaries, sorted by author date.
    """
    separator = "|||---|||"
    cmd = [
        "git",
        "log",
        f"--since={days}.days.ago",
        "--author-date-order",
        f"--pretty=format:%H{separator}%aI{separator}%s",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd=repo_path
        )
    except FileNotFoundError:
        print("Error: git command not found. Is git installed and in your PATH?")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error executing git log: {e.stderr}")
        sys.exit(1)

    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split(separator)
        if len(parts) == 3:
            commits.append(
                {"hash": parts[0], "author_date": parts[1], "subject": parts[2]}
            )
    return commits


def get_file_diffs(commit_hash, file_paths, repo_path):
    """
    Gets the diff for specific files in a given commit.
    """
    diffs = {}
    for file_path in file_paths:
        # The command will show the changes to the file in that commit
        cmd = ["git", "show", commit_hash, "--", file_path]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,  # check=False because file might not be in commit
                cwd=repo_path,
            )
            # Add diff if the command was successful and there is output
            if result.returncode == 0 and result.stdout:
                diffs[file_path] = result.stdout
        except FileNotFoundError:
            # This error is handled in get_commits, so we can pass here
            pass
    return diffs


def get_commit_stats(commit_hash, repo_path):
    """
    Gets the file change statistics (insertions/deletions) for a given commit.
    """
    cmd = ["git", "show", commit_hash, "--numstat", "--pretty="]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd=repo_path
        )
        stats = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) == 3:
                try:
                    insertions = int(parts[0]) if parts[0] != "-" else 0
                    deletions = int(parts[1]) if parts[1] != "-" else 0
                    stats.append({
                        "file": parts[2],
                        "insertions": insertions,
                        "deletions": deletions,
                    })
                except (ValueError, IndexError):
                    pass  # Ignore lines that don't parse correctly
        return stats
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []  # Return empty stats if git command fails


def analyze_work_sessions(commits, max_session_gap_hours=1):
    """
    Groups commits into sessions based on the time gap between them.
    This is for reporting purposes only.
    """
    sessions = []
    if not commits:
        return []

    current_session = [commits[0]]
    for i in range(1, len(commits)):
        if commits[i]["hours_since_previous"] <= max_session_gap_hours:
            current_session.append(commits[i])
        else:
            sessions.append(current_session)
            current_session = [commits[i]]
    sessions.append(current_session)  # Add the last session

    return sessions


def generate_work_prompt(analysis_data):
    """
    Generates the raw work analysis section of the prompt.
    """
    prompt = ""
    for i, session in enumerate(analysis_data["work_sessions"]):
        prompt += f"\n--- Session {i+1} ---\n"
        for commit in session:
            prompt += f"- Commit {commit['hash'][:7]}: {commit['subject']}\n"
            if "stats" in commit and commit["stats"]:
                total_insertions = sum(s["insertions"] for s in commit["stats"])
                total_deletions = sum(s["deletions"] for s in commit["stats"])
                prompt += f"    - Changes: {len(commit['stats'])} files changed ({total_insertions} insertions, {total_deletions} deletions)\n"

            if "tracked_file_diffs" in commit:
                for file_path, diff in commit["tracked_file_diffs"].items():
                    prompt += f"  - Diff for `{file_path}`:\n"
                    # Indent the diff for readability in the prompt
                    indented_diff = "    " + diff.replace("\n", "\n    ")
                    prompt += indented_diff + "\n"
    return prompt
    return prompt


def call_gemini_api(prompt, api_key):
    """
    Calls the Gemini API with the given prompt and returns the text response.
    """
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = subprocess.run(
            [
                "curl",
                "-s",
                "-X",
                "POST",
                "-H",
                "Content-Type: application/json",
                "-d",
                json.dumps(data),
                url,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        response_json = json.loads(response.stdout)
        return response_json["candidates"][0]["content"]["parts"][0]["text"]
    except (
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        KeyError,
        IndexError,
    ) as e:
        print(f"Error calling Gemini API: {e}")
        if isinstance(e, subprocess.CalledProcessError):
            print(f"Stderr: {e.stderr}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Analyze git repository history to estimate work."
    )
    parser.add_argument("repo_path", help="Path to the git repository to analyze.")
    parser.add_argument(
        "--days", type=int, default=30, help="The number of past days to analyze."
    )
    parser.add_argument(
        "--session-gap",
        type=float,
        default=1.0,
        help="Max hours between commits for session grouping.",
    )
    parser.add_argument(
        "--full-credit",
        type=float,
        default=1.0,
        help="Max hours for a gap to get 100% work credit.",
    )
    parser.add_argument(
        "--zero-credit",
        type=float,
        default=5.0,
        help="Base hours for a gap to get 0% work credit.",
    )
    parser.add_argument(
        "--change-baseline",
        type=int,
        default=100,
        help="Line change count that receives no bonus hours.",
    )
    parser.add_argument(
        "--change-max-score",
        type=int,
        default=500,
        help="Line change count that receives the maximum bonus hours.",
    )
    parser.add_argument(
        "--max-bonus-hours",
        type=float,
        default=5.0,
        help="Maximum bonus hours to add to the zero-credit threshold.",
    )
    args = parser.parse_args()

    print(f"Analyzing commits from the last {args.days} days in {args.repo_path}...")
    commits = get_commits(args.days, args.repo_path)

    if not commits:
        print("No commits found in the specified period.")
        return

    # Sort commits and calculate initial gaps
    commits = sorted(commits, key=lambda c: datetime.fromisoformat(c["author_date"]))
    if commits:
        commits[0]["hours_since_previous"] = 0.0
        for i in range(1, len(commits)):
            prev_commit_time = datetime.fromisoformat(commits[i - 1]["author_date"])
            current_commit_time = datetime.fromisoformat(commits[i]["author_date"])
            time_diff = current_commit_time - prev_commit_time
            commits[i]["hours_since_previous"] = round(
                time_diff.total_seconds() / 3600, 2
            )

    total_weighted_hours = 0.0
    code_file_extensions = [".ts", ".js", ".html", ".sh", ".py", ".go", ".java", ".css"]

    files_to_track = ["plan.md", "task.md"]
    print(f"Checking for changes in: {", ".join(files_to_track)}")
    for i, commit in enumerate(commits):
        # --- Data Enrichment ---
        diffs = get_file_diffs(commit["hash"], files_to_track, args.repo_path)
        if diffs:
            commit["tracked_file_diffs"] = diffs
        commit["stats"] = get_commit_stats(commit["hash"], args.repo_path)

        # --- Hour Estimation ---
        gap_hours = commit["hours_since_previous"]

        # Calculate code change score for the current commit
        code_change_score = 0
        if commit["stats"]:
            for stat in commit["stats"]:
                if any(stat["file"].endswith(ext) for ext in code_file_extensions):
                    code_change_score += stat["insertions"] + stat["deletions"]
        commit["code_change_score"] = code_change_score

        # Modulate decay based on this commit's score for the *previous* gap
        bonus_hours = 0
        if code_change_score > args.change_baseline:
            score_range = args.change_max_score - args.change_baseline
            if score_range > 0:
                progress_in_range = code_change_score - args.change_baseline
                bonus_factor = progress_in_range / score_range
                bonus_hours = min(
                    bonus_factor * args.max_bonus_hours, args.max_bonus_hours
                )

        adjusted_zero_credit_hours = args.zero_credit + bonus_hours
        commit["adjusted_zero_credit_hours"] = round(adjusted_zero_credit_hours, 2)

        # Calculate contributed hours for the gap
        contributed_hours = 0
        if gap_hours <= args.full_credit:
            contributed_hours = gap_hours
        elif args.full_credit < gap_hours < adjusted_zero_credit_hours:
            decay_range = adjusted_zero_credit_hours - args.full_credit
            position_in_range = gap_hours - args.full_credit
            decay_factor = 1.0 - (position_in_range / decay_range)
            contributed_hours = gap_hours * decay_factor

        commit["contributed_hours"] = round(contributed_hours, 2)
        total_weighted_hours += contributed_hours

    sessions = analyze_work_sessions(commits, args.session_gap)

    output_data = {
        "analysis_repo_path": args.repo_path,
        "analysis_period_days": args.days,
        "max_session_gap_hours": args.session_gap,
        "full_credit_hours": args.full_credit,
        "zero_credit_hours": args.zero_credit,
        "change_baseline": args.change_baseline,
        "change_max_score": args.change_max_score,
        "max_bonus_hours": args.max_bonus_hours,
        "estimated_hours": total_weighted_hours,
        "total_commits": len(commits),
        "work_sessions": sessions,
    }

    # Save output files in the current directory from where the script is called
    output_dir = "."

    analysis_file = os.path.join(output_dir, "work_analysis.json")
    with open(analysis_file, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"Analysis data saved to {analysis_file}")

    # --- Prompt Generation ---
    # 1. Generate the automated work summary
    work_prompt = generate_work_prompt(output_data)
    work_prompt_file = os.path.join(output_dir, "work_prompt.txt")
    with open(work_prompt_file, "w") as f:
        f.write(work_prompt)
    print(f"Automated work summary saved to {work_prompt_file}")

    # 2. Assemble the full prompt from templates
    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    try:
        with open(os.path.join(template_dir, "product_summary.md"), "r") as f:
            product_summary = f.read()
        with open(os.path.join(template_dir, "client_profile.md"), "r") as f:
            client_profile = f.read()
        with open(os.path.join(template_dir, "value_propositions.md"), "r") as f:
            value_propositions = f.read()

        full_prompt = (
            f"# Work Report for Turboheatweldingtools\n\n"
            f"## Product Summary\n{product_summary}\n\n"
            f"## Client Profile\n{client_profile}\n\n"
            f"## Key Value Delivered This Period\n{value_propositions}\n\n"
            f"## Detailed Work Analysis (Automated)\n"
            f"The following is a detailed, automated analysis of the git commit history for the period."
            f"{work_prompt}"
            f"\n---\n"
            f"**INSTRUCTION:** Based on all the information above (product, client, value propositions, and detailed commits), "
            f"generate a concise, client-facing summary of the work completed. Frame the technical achievements as tangible business value, "
            f"referencing the client's pain points and the product's goals. Emphasize how the work reduces costs, improves efficiency, and enhances system capabilities."
        )

        full_prompt_file = os.path.join(output_dir, "full_prompt.txt")
        with open(full_prompt_file, "w") as f:
            f.write(full_prompt)
        print(f"Final client-facing prompt saved to {full_prompt_file}")

        # 3. Call Gemini API and save the final response
        print("\nSending prompt to Gemini API for final summary...")
        api_key = os.environ.get("GEMINI_API_KEY")
        summary_text = call_gemini_api(full_prompt, api_key)
        if summary_text:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_filename = f"{timestamp}_client_summary.md"
            # Corrected directory name to 'responses'
            summary_path = os.path.join(
                os.path.dirname(__file__), "..", "responses", summary_filename
            )
            os.makedirs(os.path.dirname(summary_path), exist_ok=True)
            with open(summary_path, "w") as f:
                f.write(summary_text)
            print(f"Successfully generated and saved client summary to {summary_path}")

    except FileNotFoundError as e:
        print(
            f"\nWarning: Could not generate full prompt. Template file not found: {e.filename}"
        )

    print("\n--- Summary ---")
    print(f"Estimated hours worked: {output_data['estimated_hours']:.2f}")
    print(f"Total commits: {output_data['total_commits']}")
    print(f"Number of work sessions found: {len(output_data['work_sessions'])}")


if __name__ == "__main__":
    main()
