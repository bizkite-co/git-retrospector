# lambda_fns/initiation/handler.py
import boto3
import os
import json
import datetime
import logging
import subprocess
import tempfile
import shutil

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Assume git is available in the Lambda environment (e.g., via a layer)
# If git is installed directly in a custom runtime, adjust path or just use 'git'
# If using a layer, ensure the layer includes the git binary and necessary libs
# and that the path below matches the location within the layer (/opt/bin/ is common)
GIT_EXECUTABLE = os.environ.get(
    "GIT_EXECUTABLE_PATH", "git"
)  # Allow overriding via env var


def get_commit_list(repo_path, iterations=10):
    """
    Fetches the commit list from a local git repository.
    Reimplementation of the core 'git log' logic.
    """
    # Simplified git log command - adjust format as needed
    # Format: hash<SEP>date<SEP>summary
    sep = "<SEP>"
    command = [
        GIT_EXECUTABLE,
        "-C",
        repo_path,
        "log",
        f"-n{iterations}",
        f"--pretty=format:%H{sep}%cI{sep}%s",  # Hash, ISO8601 Date, Subject
    ]
    logger.info(f"Running git command: {' '.join(command)}")
    try:
        # Set HOME environment variable for git commands
        env = os.environ.copy()
        env["HOME"] = "/tmp"  # Git might need a writable home directory
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, env=env
        )
        commits = []
        stdout_lines = result.stdout.strip().split("\n")
        logger.info(
            f"Git log stdout ({len(stdout_lines)} lines): {result.stdout[:500]}..."
        )  # Log beginning of output
        for line in stdout_lines:
            if line:
                parts = line.split(sep, 2)
                if len(parts) == 3:
                    commits.append({
                        "commit_hash": parts[0],
                        "commit_date": parts[1],
                        "commit_summary": parts[2],
                    })
                else:
                    logger.warning(f"Could not parse commit line: {line}")
        logger.info(f"Fetched {len(commits)} commits.")
        return commits
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running git log: {e}")
        logger.error(f"Stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        logger.error(
            f"Git executable not found at '{GIT_EXECUTABLE}'."
            "Ensure git is available in the Lambda environment and "
            "GIT_EXECUTABLE_PATH is set correctly if needed."
        )
        raise


def lambda_handler(event, context):
    """
    Lambda handler function to initiate the retrospector workflow.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    # 1. Parse input event
    try:
        repo_owner = event["repo_owner"]
        repo_name = event["repo_name"]
        # Use HTTPS URL for cloning, authentication handled by
        # git credential helper or token
        # Construct repo_url here
        repo_url = f"https://github.com/{repo_owner}/{repo_name}.git"
        iterations = int(event.get("iterations", 10))
        # Default to 10 iterations, ensure int
        # Token might be needed for private repos,
        # handled by git credential helper ideally
        # For explicit token usage (less secure):
        # git_token = os.environ.get('GIT_TOKEN')
        # clone_url = f"https://{git_token}@github.com/{
        # repo_owner}/{repo_name}.git" if git_token else repo_url

    except KeyError as e:
        logger.error(f"Missing required key in event: {e}")
        return {"statusCode": 400, "body": json.dumps(f"Missing required key: {e}")}
    except ValueError as e:
        logger.error(f"Invalid value for iterations: {event.get('iterations')}")
        return {
            "statusCode": 400,
            "body": json.dumps(f"Invalid value for iterations: {e}"),
        }

    # 2. Get environment variables for AWS resources
    try:
        table_name = os.environ["COMMIT_STATUS_TABLE_NAME"]
        state_machine_arn = os.environ["STATE_MACHINE_ARN"]
    except KeyError as e:
        logger.error(f"Missing required environment variable: {e}")
        # This is an internal configuration error
        return {
            "statusCode": 500,
            "body": json.dumps(f"Configuration error: Missing env var {e}"),
        }

    # 3. Initialize boto3 clients
    dynamodb = boto3.resource("dynamodb")
    sfn = boto3.client("stepfunctions")
    table = dynamodb.Table(table_name)

    repo_id = f"{repo_owner}/{repo_name}"  # Still needed for DDB writes here
    temp_dir = None

    try:
        # 4. Clone the repository into /tmp
        # Lambda /tmp is 512MB by default, expandable up to 10GB
        temp_dir = tempfile.mkdtemp()
        repo_path = os.path.join(temp_dir, repo_name)
        logger.info(f"Cloning {repo_url} into {repo_path}...")
        # Use sparse checkout and shallow clone to minimize size/time if possible
        # Adjust depth based on 'iterations'
        clone_depth = iterations + 5  # Add a small buffer
        clone_command = [
            GIT_EXECUTABLE,
            "clone",
            "--depth",
            str(clone_depth),
            repo_url,
            repo_path,
        ]
        logger.info(f"Running git command: {' '.join(clone_command)}")
        # Set HOME environment variable for git commands
        env = os.environ.copy()
        env["HOME"] = "/tmp"  # Git might need a writable home directory
        subprocess.run(
            clone_command, capture_output=True, text=True, check=True, env=env
        )
        logger.info("Repository cloned successfully.")

        # 5. Fetch commit list
        commits = get_commit_list(repo_path, iterations)
        if not commits:
            logger.warning("No commits found in the repository.")
            # Consider if this should trigger an empty Step Functions
            # execution or stop here
            return {
                "statusCode": 200,
                "body": json.dumps("No commits found to process."),
            }

        # 6. Populate DynamoDB table
        logger.info(f"Writing {len(commits)} commits to DynamoDB table {table_name}...")
        with table.batch_writer() as batch:
            for commit in commits:
                batch.put_item(
                    Item={
                        "repo_id": repo_id,  # Partition Key (still needed here)
                        "commit_hash": commit["commit_hash"],  # Sort Key
                        "commit_date": commit["commit_date"],
                        "commit_summary": commit["commit_summary"],
                        "status": "PENDING",  # Initial status
                        "last_updated": datetime.datetime.utcnow().isoformat(),
                    }
                )
        logger.info("Commits written to DynamoDB.")

        # 7. Prepare input for Step Functions - SIMPLIFIED
        sfn_input = {
            "repo_url": repo_url,  # Pass only the URL
            "commits": commits,  # Pass the list of commits to the next step
        }

        # 8. Start Step Functions execution
        logger.info(
            f"""Starting Step Functions execution for ARN: {
            state_machine_arn}"""
        )

        response = sfn.start_execution(
            stateMachineArn=state_machine_arn, input=json.dumps(sfn_input)
        )
        logger.info(
            f"""Step Functions execution started: {
            response['executionArn']}"""
        )

        # 9. Return success
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Workflow initiated successfully.",
                "executionArn": response["executionArn"],
            }),
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e.returncode}")
        logger.error(f"Command: {' '.join(e.cmd)}")
        # Avoid logging token if it was part of the command/URL
        logger.error(f"Stderr: {e.stderr}")
        logger.error(f"Stdout: {e.stdout}")
        # Provide a generic error message back to the caller
        return {
            "statusCode": 500,
            "body": json.dumps("Git operation failed. Check logs for details."),
        }
    except Exception:
        logger.exception("An unexpected error occurred during initiation.")
        # Provide a generic error message back to the caller
        return {
            "statusCode": 500,
            "body": json.dumps("Internal server error. Check logs for details."),
        }

    finally:
        # Clean up the temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                # Log error but don't fail the function execution for cleanup issues
                logger.error(f"Error cleaning up temp directory {temp_dir}: {e}")
