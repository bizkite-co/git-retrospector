# Plan to Address GitHub Issue #16

## Goal

Implement robust logging and address error handling concerns in the `git-retrospector` project, as per GitHub Issue #16.

## Steps

1.  **Add Logging to `retrospector.py`:**
    *   Import the `logging` module.
    *   Configure a basic logger at the beginning of the file, including a formatter for timestamps and log levels. Start with logging to the console and consider adding file logging later.
    *   Replace `print` statements used for error reporting with `logging.error`.
    *   Add `logging.info` statements for key events (e.g., starting a run, processing a commit).
    *   Add `logging.debug` statements for detailed information (e.g., config values, Git command output).
2.  **Enhance Error Messages:**
    *   Modify the `except` blocks to include more context in the log messages.
3.  **Ask User about AWS Integration:**
    *   Ask the user if they intend to use AWS Step Functions or CloudWatch with this project.
4.  **Refactor `process_commit`:**
    *   Add a try-except block in `src/git_retrospector/commit_processor.py` around the main logic of the `process_commit` function to catch and log any exceptions.
5.  **Improve `count_failed_tests`:**
    *   Log the exception that occurs when reading the CSV and consider raising a custom exception.
6.  **Improve `create_github_issues`:**
    *   Log the exception that occurs when getting the repository.

## Implementation (in Code Mode)

The following changes will be made in Code mode:

**1. `src/git_retrospector/retrospector.py`:**

```diff
--- a/src/git_retrospector/retrospector.py
+++ b/src/git_retrospector/retrospector.py
@@ -3,11 +3,19 @@
 import csv
 import os
 import subprocess
+import logging
 from pathlib import Path

 import toml
 from pydantic import ValidationError

+# Configure logging
+logging.basicConfig(
+    level=logging.INFO,
+    format="%(asctime)s - %(levelname)s - %(message)s",
+)
+
 from git_retrospector.config import Config
 from git_retrospector.git_utils import (
     get_current_commit_hash,
@@ -36,15 +44,15 @@
          test_output_dir = str(config.test_result_dir)
      except FileNotFoundError:
          print(  # noqa: T201
-             f"Error: Config file not found: {config_file_path}\n"
+             f"Error: Config file not found: {config_file_path}\\n"
              f"Please run: './retrospector.py init {target_name} <target_repo_path>'"
          )
+         logging.error(f"Config file not found: {config_file_path}")
          return
      except (KeyError, toml.TomlDecodeError) as e:
-         print(f"Error reading config file: {e}")  # noqa: T201
+         logging.error(f"Error reading config file: {e}")
          return
      except ValidationError as e:
-         print(f"Error validating config file: {e}")  # noqa: T201
+         logging.error(f"Error validating config file: {e}")
          return

      commits_log_path = Path(config.test_result_dir) / "commits.log"
@@ -57,12 +65,14 @@
              "repository or does not exist"
          )

+        logging.info(f"Running tests for {target_name} ({iteration_count} iterations)")
+
          # Use get_current_commit_hash to get the initial HEAD *before* the loop
          current_commit = get_current_commit_hash(target_repo)
          if current_commit is None:
              return
          for i in range(iteration_count):
-             print(f"Iteration: {i}")  # noqa: T201
+             logging.info(f"Iteration: {i}")
              try:
                  commit_hash_result = subprocess.run(
                      ["git", "rev-parse", "--short", f"{current_commit}~{i}"],
@@ -71,7 +81,7 @@
                      text=True,
                      check=True,
                  )
-                 print(f"rev-parse result: {commit_hash_result}")  # noqa: T201
+                 logging.debug(f"rev-parse result: {commit_hash_result.stdout.strip()}")
                  commit_hash = commit_hash_result.stdout.strip()
                  if not commit_hash:
                      continue  # Skip this iteration
@@ -81,7 +91,8 @@
                      origin_branch, config
                  )
                  commits_log.write(f"{commit_hash}\\n")
-             except subprocess.CalledProcessError:
+             except subprocess.CalledProcessError as e:
+                 logging.error(f"Error processing commit {current_commit}~{i}: {e}")
                  continue


@@ -127,7 +138,8 @@
              reader = csv.DictReader(f)
              for row in reader:
                  if row.get("Result") == "failed":
-                     failed_count += 1
+                    failed_count += 1
+
      except Exception:
          return -1  # Indicate an error
      return failed_count
@@ -297,3 +309,4 @@
          create_issues_for_commit(args.retro_name, args.commit_hash)
      else:
          parser.print_help()
+
```

**2. `src/git_retrospector/commit_processor.py`:**

```diff
--- a/src/git_retrospector/commit_processor.py
+++ b/src/git_retrospector/commit_processor.py
@@ -1,6 +1,7 @@
 #!/usr/bin/env python3
 import os
 import subprocess
+import logging


 def process_commit(target_repo, commit_hash, test_output_dir, origin_branch, config):
@@ -13,30 +14,34 @@
         origin_branch (str): The name of the origin branch.
         config (Config): The configuration object.
     """
-    # Checkout the specific commit
-    subprocess.run(
-        ["git", "checkout", commit_hash], cwd=target_repo, check=True, capture_output=True
-    )
+    try:
+        # Checkout the specific commit
+        subprocess.run(
+            ["git", "checkout", commit_hash], cwd=target_repo, check=True, capture_output=True
+        )

-    # Run tests and capture output
-    test_command = [
-        "npm",
-        "test",
-        "--",
-        "--testNamePattern",
-        f"retro_commit_hash={commit_hash}",
-        "--outputFile",
-        f"{test_output_dir}/{commit_hash}/test-results.json",
-    ]
-    subprocess.run(test_command, cwd=target_repo, check=True, capture_output=True)
+        # Run tests and capture output
+        test_command = [
+            "npm",
+            "test",
+            "--",
+            "--testNamePattern",
+            f"retro_commit_hash={commit_hash}",
+            "--outputFile",
+            f"{test_output_dir}/{commit_hash}/test-results.json",
+        ]
+        subprocess.run(test_command, cwd=target_repo, check=True, capture_output=True)

-    # Checkout back to the origin branch
-    subprocess.run(
-        ["git", "checkout", origin_branch],
-        cwd=target_repo,
-        check=True,
-        capture_output=True,
-    )
+        # Checkout back to the origin branch
+        subprocess.run(
+            ["git", "checkout", origin_branch],
+            cwd=target_repo,
+            check=True,
+            capture_output=True,
+        )
+    except subprocess.CalledProcessError as e:
+        logging.error(f"Error processing commit {commit_hash}: {e}")
+    except Exception as e:
+        logging.error(f"An unexpected error occurred processing commit {commit_hash}: {e}")

```

**3. Improve `count_failed_tests` (in `src/git_retrospector/retrospector.py`):**

```diff
--- a/src/git_retrospector/retrospector.py
+++ b/src/git_retrospector/retrospector.py
@@ -127,8 +127,9 @@
              reader = csv.DictReader(f)
              for row in reader:
                  if row.get("Result") == "failed":
-                     failed_count += 1
-     except Exception:
+                    failed_count += 1
+     except Exception as e:
+         logging.error(f"Error reading CSV file {csv_file}: {e}")
          return -1  # Indicate an error
      return failed_count

```

**4. Improve `create_github_issues` (in `src/git_retrospector/retrospector.py`):**

```diff
--- a/src/git_retrospector/retrospector.py
+++ b/src/git_retrospector/retrospector.py
@@ -229,7 +229,8 @@

      try:
          repo = g.get_user(repo_owner).get_repo(repo_name)
-     except Exception:
+     except Exception as e:
+         logging.error(f"Error getting repository {repo_owner}/{repo_name}: {e}")
          return
      process_csv_files(repo, playwright_csv, vitest_csv)
