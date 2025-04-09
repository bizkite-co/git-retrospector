# fargate_task/process_single_commit_task.py
import os
import subprocess
import boto3
import logging
import shutil
import sys
from pathlib import Path
from botocore.exceptions import ClientError
import time
from typing import Dict, Any, Tuple, Optional

# --- Placeholder for shared code/functions ---
# TODO: Determine the best strategy for sharing code (copy, layer, package)
# For now, we might define simplified versions or placeholders here.


def run_command(command, cwd=None, env=None):
    """Runs a shell command and logs output."""
    cmd_str = " ".join(command)
    location = cwd or os.getcwd()
    logging.info(f"Running command: {cmd_str} in {location}")
    try:
        process = subprocess.run(
            command, check=True, capture_output=True, text=True, cwd=cwd, env=env
        )
        logging.info(f"Command stdout:\n{process.stdout}")
        if process.stderr:
            logging.warning(f"Command stderr:\n{process.stderr}")
        return True, process.stdout, process.stderr
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed with exit code {e.returncode}")
        logging.error(f"Stdout:\n{e.stdout}")
        logging.error(f"Stderr:\n{e.stderr}")
        return False, e.stdout, e.stderr
    except Exception as e:
        logging.error(f"An unexpected error occurred running command: {e}")
        return False, "", str(e)


def parse_test_results(output_dir: Path) -> Tuple[int, int]:
    """
    Parses test results from files in the output directory.
    Placeholder implementation. Needs adaptation based on actual
    test runner output format.
    """
    logging.info(f"Parsing test results from {output_dir}...")
    # TODO: Implement actual parsing logic based on the test runner output format
    # For now, simulate some results
    total_tests = 10  # Placeholder
    failed_tests = 1  # Placeholder
    logging.info(f"Parsing complete: Total={total_tests}, Failed={failed_tests}")
    return total_tests, failed_tests


# --- End Placeholder Section ---


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],  # Ensure logs go to stdout for CloudWatch
)

# Define constants for environment variable names
REPO_OWNER_ENV = "REPO_OWNER"
REPO_NAME_ENV = "REPO_NAME"
REPO_URL_ENV = "REPO_URL"
COMMIT_HASH_ENV = "COMMIT_HASH_TO_PROCESS"
TABLE_NAME_ENV = "DYNAMODB_TABLE_NAME"
BUCKET_NAME_ENV = "S3_BUCKET_NAME"
TEST_COMMAND_ENV = "TEST_COMMAND"

# Define local paths within the container
BASE_WORK_DIR = Path("/app")
REPO_DIR = BASE_WORK_DIR / "repo"
OUTPUT_DIR = BASE_WORK_DIR / "output"


def get_task_config() -> Dict[str, str]:
    """Retrieves and validates required configuration from environment variables."""
    config = {
        "repo_owner": os.environ.get(REPO_OWNER_ENV),
        "repo_name": os.environ.get(REPO_NAME_ENV),
        "repo_url": os.environ.get(REPO_URL_ENV),
        "commit_hash": os.environ.get(COMMIT_HASH_ENV),
        "table_name": os.environ.get(TABLE_NAME_ENV),
        "bucket_name": os.environ.get(BUCKET_NAME_ENV),
        "test_command_str": os.environ.get(
            TEST_COMMAND_ENV, "echo 'No test command provided'"
        ),
    }

    required_vars_map = {
        REPO_OWNER_ENV: config["repo_owner"],
        REPO_NAME_ENV: config["repo_name"],
        REPO_URL_ENV: config["repo_url"],
        COMMIT_HASH_ENV: config["commit_hash"],
        TABLE_NAME_ENV: config["table_name"],
        BUCKET_NAME_ENV: config["bucket_name"],
    }
    missing_vars = [k for k, v in required_vars_map.items() if not v]
    if missing_vars:
        msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logging.error(msg)
        raise ValueError(msg)

    config["repo_id"] = f"{config['repo_owner']}/{config['repo_name']}"
    logging.info(
        f"Processing commit {config['commit_hash']} for repository {config['repo_id']}"
    )
    return config


def initialize_aws_clients(table_name: str) -> Tuple[Any, Any, Any]:
    """Initializes and returns Boto3 clients for DynamoDB and S3."""
    try:
        dynamodb = boto3.resource("dynamodb")
        s3_client = boto3.client("s3")
        table = dynamodb.Table(table_name)
        return dynamodb, s3_client, table
    except Exception as e:
        logging.error(f"Failed to initialize AWS clients: {e}")
        raise


def update_dynamodb_status(
    table, repo_id: str, commit_hash: str, status: str, details: Optional[Dict] = None
) -> bool:
    """Updates the status of a commit in DynamoDB."""
    logging.info(f"Updating DDB: repo={repo_id}, commit={commit_hash}, status={status}")
    try:
        update_expression = "SET #status_attr = :status_val, last_updated = :updated_ts"
        expression_attribute_names = {"#status_attr": "status"}
        expression_attribute_values = {
            ":status_val": status,
            ":updated_ts": int(time.time()),
        }

        if details:
            for key, value in details.items():
                if value is not None:  # Only add attributes if they have a value
                    attr_name = f"#attr_{key}"
                    val_name = f":val_{key}"
                    update_expression += f", {attr_name} = {val_name}"
                    expression_attribute_names[attr_name] = key
                    expression_attribute_values[val_name] = value

        table.update_item(
            Key={"repo_id": repo_id, "commit_hash": commit_hash},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ConditionExpression=(
                "attribute_exists(repo_id) " "AND attribute_exists(commit_hash)"
            ),
        )
        logging.info("DynamoDB update successful.")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            logging.error(
                f"DDB item not found for {repo_id}/{commit_hash}. Cannot update."
            )
        else:
            logging.error(f"Failed to update DynamoDB: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during DynamoDB update: {e}")
        return False


def upload_to_s3(s3_client, bucket_name: str, local_path: Path, s3_prefix: str) -> bool:
    """Uploads the contents of a local directory to S3."""
    logging.info(f"Uploading {local_path} to s3://{bucket_name}/{s3_prefix}")
    try:
        for item in local_path.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(local_path)
                s3_key = f"{s3_prefix}/{relative_path}"
                logging.debug(f"Uploading {item} to {s3_key}")
                s3_client.upload_file(str(item), bucket_name, s3_key)
        logging.info("S3 upload successful.")
        return True
    except ClientError as e:
        logging.error(f"Failed to upload to S3: {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during S3 upload: {e}")
        return False


def prepare_local_dirs():
    """Creates local directories for repo cloning and output."""
    logging.info(f"Creating local directories: {REPO_DIR}, {OUTPUT_DIR}")
    REPO_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def perform_git_operations(repo_url: str, commit_hash: str):
    """Clones the repository and checks out the specified commit."""
    logging.info(f"Cloning repository {repo_url} into {REPO_DIR}")
    # TODO: Handle private repos / credentials if necessary
    # Note: Cloning full repo first, then checkout. Optimize later if needed.
    clone_command = ["git", "clone", repo_url, str(REPO_DIR)]
    success, _, stderr = run_command(clone_command)
    if not success:
        raise RuntimeError(f"Failed to clone repository: {stderr}")

    logging.info(f"Checking out commit {commit_hash}")
    checkout_command = ["git", "checkout", commit_hash]
    success, _, stderr = run_command(checkout_command, cwd=REPO_DIR)
    if not success:
        raise RuntimeError(f"Failed to checkout commit {commit_hash}: {stderr}")


def run_tests(test_command_str: str) -> bool:
    """Runs the configured test command(s)."""
    logging.info(f"Running test command: {test_command_str}")
    test_command_list = test_command_str.split()
    test_env = os.environ.copy()
    test_env["TEST_OUTPUT_DIR"] = str(OUTPUT_DIR)
    success, _, stderr = run_command(test_command_list, cwd=REPO_DIR, env=test_env)
    if not success:
        logging.warning(
            f"Test command execution failed or reported errors. Stderr: {stderr}"
        )
        # Return False, but allow processing to continue to parse/upload partial results
        return False
    return True


def process_results(
    s3_client, bucket_name: str, repo_owner: str, repo_name: str, commit_hash: str
) -> Tuple[Optional[int], Optional[int], Optional[str], Optional[str]]:
    """Parses test results and uploads them to S3. Returns results and error message."""
    total_tests, failed_tests = None, None
    s3_output_path = None
    error_message = None  # Changed variable name for clarity

    logging.info("Parsing test results...")
    try:
        total_tests, failed_tests = parse_test_results(OUTPUT_DIR)
        logging.info(f"Parsed results: Total={total_tests}, Failed={failed_tests}")
    except Exception as e:
        error_message = f"Failed to parse test results: {e}"
        logging.error(error_message)
        # Continue to upload, but parsing failed

    s3_prefix = f"{repo_owner}/{repo_name}/{commit_hash}"
    if upload_to_s3(s3_client, bucket_name, OUTPUT_DIR, s3_prefix):
        s3_output_path = f"s3://{bucket_name}/{s3_prefix}/"
        logging.info(f"Results uploaded to {s3_output_path}")
    else:
        # Prioritize upload error message if parsing also failed
        upload_error = "Failed to upload results to S3."
        error_message = error_message or upload_error
        logging.error(upload_error)
        # s3_output_path remains None

    return total_tests, failed_tests, s3_output_path, error_message


def cleanup_local_dirs():
    """Removes the temporary local directories."""
    logging.info("Cleaning up local directories...")
    try:
        if REPO_DIR.exists():
            shutil.rmtree(REPO_DIR)
            logging.info(f"Removed directory: {REPO_DIR}")
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)
            logging.info(f"Removed directory: {OUTPUT_DIR}")
    except Exception as e:
        logging.warning(f"Failed to cleanup local directories: {e}")


def main():
    """Main processing logic for the Fargate task."""
    start_time = time.time()
    logging.info("Starting Fargate task processing...")
    config = None
    table = None
    final_status = "FAILED"
    update_success = False
    exit_code = 1  # Default to failure exit code
    # Initialize result variables outside the try block
    total_tests, failed_tests, s3_path, error_message = None, None, None, None

    try:
        # 1. Get Configuration
        config = get_task_config()

        # 2. Initialize AWS Clients
        _, s3_client, table = initialize_aws_clients(config["table_name"])

        # 3. Update Status to RUNNING
        if not update_dynamodb_status(
            table, config["repo_id"], config["commit_hash"], "RUNNING"
        ):
            # If we can't even mark as running, abort early
            raise RuntimeError("Failed to set initial RUNNING status in DynamoDB.")

        # --- Core Processing ---
        prepare_local_dirs()
        perform_git_operations(config["repo_url"], config["commit_hash"])
        test_success = run_tests(config["test_command_str"])
        logging.info("Test success:", test_success)
        # Even if tests fail (test_success=False), proceed to parse/upload results

        total_tests, failed_tests, s3_path, processing_error = process_results(
            s3_client,
            config["bucket_name"],
            config["repo_owner"],
            config["repo_name"],
            config["commit_hash"],
        )
        # --- End Core Processing ---

        # Determine final status based on errors
        if processing_error:
            final_status = "FAILED"
            error_message = processing_error  # Assign the specific error
        else:
            final_status = "COMPLETE"
            error_message = None  # Clear error if successful
            logging.info("Task completed successfully.")

    except Exception as e:
        logging.error(f"Critical error during task execution: {e}", exc_info=True)
        final_status = "FAILED"
        # Use the exception as the error message if no specific one was set
        error_message = error_message or f"Unhandled exception: {str(e)}"
        # Ensure results from partial success are not reported if a
        # critical error occurred
        total_tests, failed_tests, s3_path = None, None, None

    finally:
        if config and table:
            # 10. Update Final Status in DynamoDB
            logging.info(f"Updating final status to {final_status} in DynamoDB.")
            details_to_update = {
                "total_tests": total_tests,
                "failed_tests": failed_tests,
                "s3_output_path": s3_path,
                "error_message": error_message,  # Use the determined error message
                "processing_duration_ms": int((time.time() - start_time) * 1000),
            }
            details_to_update = {
                k: v for k, v in details_to_update.items() if v is not None
            }

            update_success = update_dynamodb_status(
                table,
                config["repo_id"],
                config["commit_hash"],
                final_status,
                details_to_update,
            )
            if not update_success:
                logging.error("CRITICAL: Failed to update final status in DynamoDB.")
        else:
            logging.error(
                "CRITICAL: Config or DDB table not available for final update."
            )
            update_success = False  # Ensure exit code reflects failure

        # 11. Cleanup Local Filesystem
        cleanup_local_dirs()

        end_time = time.time()
        logging.info(
            f"Fargate task finished in {end_time - start_time:.2f} seconds. "
            f"Final status: {final_status}"
        )

        # Exit with 0 if COMPLETE and final DDB update succeeded, else 1
        exit_code = 0 if final_status == "COMPLETE" and update_success else 1
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
