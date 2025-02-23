import subprocess
import os
import sys
import argparse
from .parser import parse_test_results

def get_original_branch(target_repo):
    try:
        result = subprocess.run(
            ['git', 'symbolic-ref', '--short', 'HEAD'],
            cwd=target_repo,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting original branch: {e}", file=sys.stderr)
        return None

def get_current_commit_hash(target_repo):
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=target_repo,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting current commit hash: {e}", file=sys.stderr)
        return None

def run_vitest(target_repo, output_dir):
    vitest_log = os.path.join(output_dir, 'vitest.log')
    vitest_output = os.path.join(output_dir, 'vitest.xml')
    print("  Running Vitest...")
    with open(vitest_log, 'w') as vitest_log_file:
        try:
            subprocess.run(
                ['npx', 'vitest', 'run', '--reporter=junit', f'--outputFile={vitest_output}'],
                cwd=target_repo,
                stdout=vitest_log_file,
                stderr=subprocess.STDOUT,
                check=True,
                text=True
            )
        except subprocess.CalledProcessError:
            # vitest returns non-zero exit code on test failure
            pass

def run_playwright(target_repo, output_dir):
    playwright_log = os.path.join(output_dir, 'playwright.log')
    playwright_output = os.path.join(output_dir, 'playwright.xml')
    print("  Running Playwright...")
    with open(playwright_log, 'w') as playwright_log_file:
        try:
            subprocess.run(
                ['npx', 'playwright', 'test', '--reporter=junit'],
                cwd=target_repo,
                env={**os.environ, 'PLAYWRIGHT_JUNIT_OUTPUT_NAME': playwright_output},
                stdout=playwright_log_file,
                stderr=subprocess.STDOUT,
                check=True,
                text=True
            )
        except subprocess.CalledProcessError:
            # playwright returns non-zero exit code on test failure
            pass

def process_commit(target_repo, commit_hash, output_base, origin_branch):
    output_dir = os.path.join(output_base, commit_hash)
    os.makedirs(output_dir, exist_ok=True)

    vitest_output = os.path.join(output_dir, 'vitest.xml')
    playwright_output = os.path.join(output_dir, 'playwright.xml')

    print(f"Processing commit {commit_hash}")

    if os.path.exists(vitest_output) and os.path.exists(playwright_output):
        print("  Skipping - output files exist")
        return

    if origin_branch is None:
        print("  Cannot checkout original branch (not determined). Skipping checkout.")
        return

    try:
        subprocess.run(
            ['git', 'checkout', '--force', commit_hash],
            cwd=target_repo,
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"  Failed to checkout commit: {commit_hash}", file=sys.stderr)
        return

    run_vitest(target_repo, output_dir)
    run_playwright(target_repo, output_dir)

    try:
        subprocess.run(
            ['git', 'checkout', '--force', origin_branch],
            cwd=target_repo,
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"  Failed to checkout original branch", file=sys.stderr)

def run_tests(target_repo, iteration_count):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_base = os.path.join(script_dir, 'commit-test-results')

    print(f"Script started")
    print(f"Target repository: {target_repo}")
    print(f"Script directory: {script_dir}")
    print(f"Output base: {output_base}")

    if not os.path.isdir(target_repo):
        print(f"Error: Target repo directory {target_repo} does not exist", file=sys.stderr)
        return

    origin_branch = get_original_branch(target_repo)
    if origin_branch is None:
        print("Could not determine original branch. Using HEAD~{i} relative to current commit.")

    os.makedirs(output_base, exist_ok=True)

    for i in range(iteration_count):
        try:
            # Use get_current_commit_hash to get the initial HEAD
            current_commit = get_current_commit_hash(target_repo)
            if current_commit is None:
                print("Failed to get current commit hash. Exiting.")
                return

            commit_hash_result = subprocess.run(
                ['git', 'rev-parse', '--short', f'{current_commit}~{i}'],
                cwd=target_repo,
                capture_output=True,
                text=True,
                check=True
            )
            commit_hash = commit_hash_result.stdout.strip()
            if not commit_hash:
                print(f"Error: rev-parse returned empty string for commit {current_commit}~{i}")
                continue  # Skip this iteration
            process_commit(target_repo, commit_hash, output_base, origin_branch)

        except subprocess.CalledProcessError as e:
            print(f"Error getting commit hash: {e}", file=sys.stderr)
            continue

    print(f"Test runs completed. Results stored in {output_base}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests on a range of commits and parse results.")
    parser.add_argument("target_repo", help="Path to the target repository")
    parser.add_argument("-i", "--iterations", type=int, default=10, help="Number of iterations (default: 10)")
    parser.add_argument("-c", "--commit_dir", help="Specific commit directory to process")  # Add commit_dir argument
    args = parser.parse_args()

    run_tests(args.target_repo, args.iterations)
    parse_test_results(args.commit_dir)  # Call parse_test_results with the commit_dir