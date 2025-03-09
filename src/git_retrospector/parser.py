import os
import json
import logging
import xml.etree.ElementTree as ET


def process_commit_results(commit_dir):
    """
    Processes the test results for a single commit, extracting error
    information and saving it to a JSON file.
    """
    logging.info(f"Processing commit: {os.path.basename(commit_dir)}")
    tool_summary_dir = os.path.join(commit_dir, "tool-summary")
    junit_xml_path = os.path.join(commit_dir, "playwright.xml")

    if os.path.exists(junit_xml_path):
        try:
            errors = {}
            tree = ET.parse(junit_xml_path)
            root = tree.getroot()
            for testcase in root.findall(".//testcase"):
                test_name = testcase.get("name")
                failure = testcase.find("failure")
                error = testcase.find("error")
                if failure is not None:
                    message = failure.get("message")
                    stack_trace = failure.text
                    errors[test_name] = {"error": message, "stack_trace": stack_trace}
                elif error is not None:
                    message = error.get("message")
                    stack_trace = error.text
                    errors[test_name] = {"error": message, "stack_trace": stack_trace}

            if errors:
                errors_json_path = os.path.join(tool_summary_dir, "errors.json")
                with open(errors_json_path, "w") as f:
                    json.dump(errors, f, indent=2)
                logging.info(f"Wrote errors to {errors_json_path}")

        except ET.ParseError as e:
            logging.error(f"Error parsing XML for {os.path.basename(commit_dir)}: {e}")
        except Exception as e:
            logging.error(
                f"Error processing commit {os.path.basename(commit_dir)}: {e}"
            )
    else:
        logging.warning(
            f"playwright.xml not found for commit: {os.path.basename(commit_dir)}"
        )


def process_retro(retro):
    """
    Processes the test results for a given retro, extracting error information
    and saving it to individual JSON files.
    """
    logging.info(f"Processing retro: {retro.name}")
    test_output_dir = retro.get_test_output_dir()

    if not os.path.exists(test_output_dir):
        logging.warning(f"Test output directory not found: {test_output_dir}")
        return

    for commit_hash in os.listdir(test_output_dir):
        commit_dir = os.path.join(test_output_dir, commit_hash)
        if os.path.isdir(commit_dir):
            process_commit_results(commit_dir)
