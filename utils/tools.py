from langchain_core.tools import tool
import shlex
import requests
import subprocess
import sys
import tempfile
import os
from typing import Optional
from .logger import setup_logger, log_function_call
from utils.parsers import remove_script_tags
from .langsmith_utils import langsmith_trace, add_trace_tags, add_trace_metadata


logger = setup_logger(__name__)


@tool
@langsmith_trace(
    name="make_curl_request",
    run_type="tool",
    tags=["http", "curl", "external_api"],
    metadata={"tool_type": "http_client"},
)
@log_function_call(logger)
def make_curl_request(curl_request: str):
    """Use this endpoint to make curl requests.
    This returns a detailed response along wiht the headers and all.

    Args:
        curl_request (str): The complete and correct curl request
    """
    logger.info(f"Received curl request: {curl_request}")
    add_trace_metadata({"curl_command": curl_request})
    add_trace_tags(["curl_request", "http_call"])

    try:
        tokens = shlex.split(curl_request)
        logger.info(f"Parsed tokens: {tokens}")
        add_trace_metadata({"parsed_tokens_count": len(tokens)})
    except Exception as e:
        logger.error(f"Failed to parse curl command: {e}")
        add_trace_tags(["parse_error"])
        add_trace_metadata({"parse_error": str(e)})
        return {"error": f"Failed to parse curl command: {str(e)}"}

    if tokens[0].lower() != "curl":
        logger.error("Invalid curl command - does not start with 'curl'")
        add_trace_tags(["invalid_command"])
        return {"error": "Not a valid curl command"}

    url = None
    method = "GET"
    headers = {}
    data = None
    i = 1

    logger.info("Parsing curl command parameters...")
    while i < len(tokens):
        token = tokens[i]
        logger.debug(f"Processing token: {token}")

        if token in ["-X", "--request"]:
            i += 1
            method = tokens[i].upper()
            logger.info(f"Set method to: {method}")
        elif token in ["-H", "--header"]:
            i += 1
            header = tokens[i]
            if ":" in header:
                k, v = header.split(":", 1)
                headers[k.strip()] = v.strip()
                logger.info(f"Added header: {k.strip()}: {v.strip()}")
        elif token in ["-d", "--data", "--data-raw", "--data-binary", "--data-ascii"]:
            i += 1
            data = tokens[i]
            logger.info(f"Set data: {data}")
            if method == "GET":
                method = "POST"
                logger.info("Changed method to POST due to data parameter")
        elif token.startswith("http"):
            url = token
            logger.info(f"Set URL to: {url}")
        i += 1

    if not url:
        logger.error("No URL found in curl command")
        add_trace_tags(["no_url_error"])
        return {"error": "No URL found in curl command"}

    # Add request metadata to trace
    add_trace_metadata(
        {
            "http_method": method,
            "target_url": url,
            "headers_count": len(headers),
            "has_data": data is not None,
        }
    )
    add_trace_tags([f"method_{method.lower()}", "parsed_successfully"])

    logger.info(f"Making {method} request to {url}")
    logger.info(f"Headers: {headers}")
    logger.info(f"Data: {data}")

    try:
        response = requests.request(method, url, headers=headers, data=data)

        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
        }

        logger.info(f"Request successful - Status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        logger.info(f"Response body length: {len(response.text)} characters")

        # Add response metadata to trace
        add_trace_metadata(
            {
                "response_status": response.status_code,
                "response_size": len(response.text),
                "response_headers_count": len(response.headers),
            }
        )
        add_trace_tags([f"status_{response.status_code}", "request_successful"])

        body_preview = (
            response.text[:500] + "..." if len(response.text) > 500 else response.text
        )
        logger.debug(f"Response body preview: {body_preview}")

        return result

    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        add_trace_tags(["request_failed"])
        add_trace_metadata({"request_error": str(e)})
        return {"error": str(e)}


@langsmith_trace(
    name="get_page_content",
    run_type="tool",
    tags=["http", "page_content", "data_retrieval"],
    metadata={"tool_type": "content_fetcher"},
)
def get_page_content(url: str):
    logger.info(f"Getting page content from URL: {url}")
    add_trace_metadata({"source_url": url})
    add_trace_tags(["content_fetch", "http_get"])

    try:
        response = requests.get(url)
        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
        }

        logger.info(f"Request successful - Status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        logger.info(f"Response body length: {len(response.text)} characters")

        # Add response metadata to trace
        add_trace_metadata(
            {
                "response_status": response.status_code,
                "content_length": len(response.text),
                "content_type": response.headers.get("content-type", "unknown"),
            }
        )
        add_trace_tags([f"status_{response.status_code}", "content_retrieved"])

        body_preview = response.text
        logger.debug(f"Response body preview: {body_preview}")

        return str(result)

    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        add_trace_tags(["content_fetch_failed"])
        add_trace_metadata({"fetch_error": str(e)})
        return {"error": str(e)}


@tool
@langsmith_trace(
    name="execute_python_code",
    run_type="tool",
    tags=["python", "code_execution", "dynamic_execution"],
    metadata={"tool_type": "code_executor"},
)
@log_function_call(logger)
def execute_python_code(python_code: str, file_path):
    """Execute Python code provided as a string and return the output.

    Args:
        python_code (str): The Python code to execute, give the complete python code as it will be run normally, it is a normal python program that will be run via command line.
        file_path (str): Path where to save the code file.

    Returns:
        dict: Contains the execution result, output, and any errors
    """
    logger.info("Executing Python code")
    add_trace_metadata(
        {"code_length": len(python_code), "has_custom_path": file_path is not None}
    )
    add_trace_tags(["code_execution", "python_exec"])

    temp_file_path = None
    should_cleanup = False

    try:
        if file_path:
            # Use the provided file path
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write code to the specified file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(python_code)

            execution_file_path = file_path
            logger.info(f"Created code file at: {file_path}")
            add_trace_tags(["persistent_file"])
        else:
            # Create a temporary file to write the Python code
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as temp_file:
                temp_file.write(python_code)
                temp_file_path = temp_file.name
                execution_file_path = temp_file_path
                should_cleanup = True

            logger.info(f"Created temporary file: {temp_file_path}")
            add_trace_tags(["temporary_file"])

        # Execute the Python code using subprocess
        result = subprocess.run(
            [sys.executable, execution_file_path],
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout to prevent hanging
        )

        # Clean up the temporary file only if it was temporary
        if should_cleanup and temp_file_path:
            os.unlink(temp_file_path)
            temp_file_path = None

        execution_result = {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
            "file_path": execution_file_path if not should_cleanup else None,
        }

        logger.info(f"Code execution completed with return code: {result.returncode}")
        logger.info(f"Stdout length: {len(result.stdout)} characters")
        logger.info(f"Stderr length: {len(result.stderr)} characters")

        # Add execution metadata to trace
        add_trace_metadata(
            {
                "execution_success": result.returncode == 0,
                "stdout_length": len(result.stdout),
                "stderr_length": len(result.stderr),
                "return_code": result.returncode,
            }
        )

        if result.returncode == 0:
            add_trace_tags(["execution_successful"])
        else:
            add_trace_tags(["execution_failed"])

        return execution_result

    except subprocess.TimeoutExpired:
        logger.error("Code execution timed out")
        add_trace_tags(["execution_timeout"])
        add_trace_metadata({"timeout_error": True})
        # Clean up the temporary file only if it was temporary
        if should_cleanup and temp_file_path:
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
        return {
            "error": "Code execution timed out (30 seconds)",
            "return_code": -1,
            "success": False,
        }
    except Exception as e:
        logger.error(f"Code execution failed: {str(e)}")
        add_trace_tags(["execution_error"])
        add_trace_metadata({"execution_error": str(e)})
        # Clean up the temporary file only if it was temporary
        if should_cleanup and temp_file_path:
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
        return {"error": str(e), "return_code": -1, "success": False}


@tool
@langsmith_trace(
    name="git_commit_and_push",
    run_type="tool",
    tags=["git", "version_control", "commit", "push"],
    metadata={"tool_type": "git_operations"},
)
@log_function_call(logger)
def git_commit_and_push(commit_message: str, branch: Optional[str] = None):
    """Commit current changes and push them to GitHub.

    Args:
        commit_message (str): The commit message for the changes
        branch (str, optional): The branch to push to. If not provided, pushes to current branch.

    Returns:
        dict: Contains the git operation results and any output/errors
    """
    logger.info(f"Starting git commit and push with message: {commit_message}")
    add_trace_metadata({"commit_message": commit_message, "target_branch": branch})
    add_trace_tags(["git_commit", "git_push"])

    try:
        # Get current working directory
        cwd = os.getcwd()
        logger.info(f"Working in directory: {cwd}")

        # Step 1: Add all changes including new files and directories
        logger.info(
            "Adding all changes to git (including new files and directories)..."
        )

        # First, add all tracked and untracked files and directories
        add_all_result = subprocess.run(
            ["git", "add", "-A"], cwd=cwd, capture_output=True, text=True, timeout=30
        )

        if add_all_result.returncode != 0:
            logger.error(f"Git add -A failed: {add_all_result.stderr}")
            add_trace_tags(["git_add_failed"])
            return {
                "success": False,
                "error": f"Git add -A failed: {add_all_result.stderr}",
                "step": "add",
            }

        # Also run git add . to ensure current directory and subdirectories are included
        add_current_result = subprocess.run(
            ["git", "add", "."], cwd=cwd, capture_output=True, text=True, timeout=30
        )

        if add_current_result.returncode != 0:
            logger.error(f"Git add . failed: {add_current_result.stderr}")
            add_trace_tags(["git_add_current_failed"])
            return {
                "success": False,
                "error": f"Git add . failed: {add_current_result.stderr}",
                "step": "add",
            }

        logger.info("Git add operations successful")

        # Step 2: Check if there are any changes to commit
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if not status_result.stdout.strip():
            logger.info("No changes to commit")
            add_trace_tags(["no_changes"])
            return {
                "success": True,
                "message": "No changes to commit",
                "step": "status_check",
            }

        # Step 3: Commit changes
        logger.info(f"Committing changes with message: {commit_message}")
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if commit_result.returncode != 0:
            logger.error(f"Git commit failed: {commit_result.stderr}")
            add_trace_tags(["git_commit_failed"])
            return {
                "success": False,
                "error": f"Git commit failed: {commit_result.stderr}",
                "step": "commit",
            }

        logger.info("Git commit successful")
        commit_output = commit_result.stdout

        # Step 4: Push to remote
        if branch:
            push_command = ["git", "push", "origin", branch]
            logger.info(f"Pushing to specific branch: {branch}")
        else:
            push_command = ["git", "push"]
            logger.info("Pushing to current branch")

        push_result = subprocess.run(
            push_command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,  # Longer timeout for push operations
        )

        if push_result.returncode != 0:
            logger.error(f"Git push failed: {push_result.stderr}")
            add_trace_tags(["git_push_failed"])
            return {
                "success": False,
                "error": f"Git push failed: {push_result.stderr}",
                "step": "push",
                "commit_output": commit_output,
            }

        logger.info("Git push successful")
        push_output = push_result.stdout

        # Success - return all outputs
        result = {
            "success": True,
            "commit_message": commit_message,
            "commit_output": commit_output,
            "push_output": push_output,
            "target_branch": branch or "current branch",
        }

        logger.info("Git commit and push completed successfully")
        add_trace_metadata(
            {
                "operation_success": True,
                "commit_completed": True,
                "push_completed": True,
            }
        )
        add_trace_tags(["git_success", "commit_and_push_completed"])

        return result

    except subprocess.TimeoutExpired as e:
        logger.error(f"Git operation timed out: {e}")
        add_trace_tags(["git_timeout"])
        add_trace_metadata({"timeout_error": str(e)})
        return {
            "success": False,
            "error": f"Git operation timed out: {str(e)}",
            "step": "timeout",
        }
    except Exception as e:
        logger.error(f"Git operation failed: {str(e)}")
        add_trace_tags(["git_operation_error"])
        add_trace_metadata({"git_error": str(e)})
        return {"success": False, "error": str(e), "step": "exception"}
