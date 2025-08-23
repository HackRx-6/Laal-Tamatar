from langchain_core.tools import tool
import shlex
import requests
import subprocess
import sys
import tempfile
import os
from typing import Optional
from .logger import setup_logger, log_function_call
from .langsmith_utils import langsmith_trace, add_trace_tags, add_trace_metadata
import chromadb
from langchain_text_splitters import CharacterTextSplitter
import uuid
from dotenv import load_dotenv

load_dotenv()


logger = setup_logger(__name__)


def get_azure_embedding_function():
    """Create a custom embedding function using Azure OpenAI that's compatible with ChromaDB."""
    import requests

    api_key = os.getenv("AZURE_KEY")
    embedding_uri = os.getenv("AZURE_EMBEDDING_URI")

    if not api_key:
        raise ValueError(
            "Azure OpenAI API key (AZURE_KEY) not found in environment variables"
        )

    if not embedding_uri:
        raise ValueError(
            "Azure OpenAI embedding URI (AZURE_EMBEDDING_URI) not found in environment variables"
        )

    class AzureOpenAIEmbeddingFunction:
        def __call__(self, input):
            """Call the Azure OpenAI embedding API."""
            headers = {"api-key": api_key, "Content-Type": "application/json"}

            # Handle both single text and list of texts
            if isinstance(input, str):
                texts = [input]
            else:
                texts = input

            embeddings = []
            for text in texts:
                data = {"input": text, "model": "text-embedding-3-large"}

                response = requests.post(embedding_uri, headers=headers, json=data)

                if response.status_code == 200:
                    result = response.json()
                    embedding = result["data"][0]["embedding"]
                    embeddings.append(embedding)
                else:
                    raise Exception(
                        f"Azure OpenAI API call failed: {response.status_code} - {response.text}"
                    )

            return embeddings if isinstance(input, list) else embeddings[0]

    return AzureOpenAIEmbeddingFunction()


@tool
@langsmith_trace(
    name="make_curl_request",
    run_type="tool",
    tags=["http", "curl", "external_api"],
    metadata={"tool_type": "http_client"},
)
@log_function_call(logger)
def make_curl_request(curl_request: str, query: str):
    """Use this endpoint to make curl requests.
    This returns a detailed response along with the headers and all.
    If the response of the curl_request is very large, a vector search is performed with the query otherwise the direct response is returned.
    Args:
        curl_request (str): The complete and correct curl request
        query (str): A short description of what you are looking for in the request's response.
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

        # Check if response is large enough to warrant vector search
        if len(response.text) > 200000:
            logger.info("Response is large (>200k chars), performing vector search")
            add_trace_tags(["large_response", "vector_search"])

            try:
                # Get Azure OpenAI embedding function
                embedding_function = get_azure_embedding_function()

                # Split the text into chunks using LangChain Character Text Splitter
                text_splitter = CharacterTextSplitter(
                    chunk_size=8123, chunk_overlap=0, separator="\n"
                )
                chunks = text_splitter.split_text(response.text)

                logger.info(f"Split response into {len(chunks)} chunks")
                add_trace_metadata({"chunks_count": len(chunks)})

                # Generate embeddings for all chunks
                logger.info(
                    "Generating embeddings using Azure OpenAI text-embedding-3-large"
                )
                chunk_embeddings = embedding_function(chunks)

                # Initialize ChromaDB client
                client = chromadb.Client()
                collection_name = f"curl_response_{uuid.uuid4().hex[:8]}"
                collection = client.create_collection(name=collection_name)

                # Add chunks to ChromaDB with pre-computed embeddings
                documents = []
                metadatas = []
                ids = []
                embeddings = []

                for i, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
                    documents.append(chunk)
                    metadatas.append({"chunk_id": i, "source": url})
                    ids.append(f"chunk_{i}")
                    embeddings.append(embedding)

                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings,
                )

                # Generate embedding for the query
                query_embedding = embedding_function([query])[0]

                # Query the collection to find most relevant chunks
                query_results = collection.query(
                    query_embeddings=[query_embedding], n_results=min(5, len(chunks))
                )

                # Get the top 5 chunks and join them
                relevant_chunks = (
                    query_results["documents"][0] if query_results["documents"] else []
                )
                filtered_response = "\n\n".join(relevant_chunks)

                logger.info(
                    f"Vector search returned {len(relevant_chunks)} relevant chunks"
                )
                add_trace_metadata({"relevant_chunks_count": len(relevant_chunks)})
                add_trace_tags(["vector_search_successful", "azure_embeddings"])

                # Update the result with filtered content
                result["body"] = filtered_response
                result["original_size"] = len(response.text)
                result["filtered_size"] = len(filtered_response)
                result["used_vector_search"] = True
                result["embedding_model"] = "text-embedding-3-large"

            except Exception as vector_error:
                logger.error(f"Vector search failed: {str(vector_error)}")
                add_trace_tags(["vector_search_failed"])
                add_trace_metadata({"vector_error": str(vector_error)})
                # Fall back to truncated response
                result["body"] = (
                    response.text[:200000] + "\n\n[Response truncated due to length]"
                )
                result["used_vector_search"] = False
                result["vector_error"] = str(vector_error)
        else:
            # Response is small enough, return as is
            result["used_vector_search"] = False

        body_preview = (
            result["body"][:500] + "..."
            if len(result["body"]) > 500
            else result["body"]
        )
        logger.debug(f"Response body preview: {body_preview}")

        return result

    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        add_trace_tags(["request_failed"])
        add_trace_metadata({"request_error": str(e)})
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


@tool
@langsmith_trace(
    name="get_github_repo_tree",
    run_type="tool",
    tags=["github", "api", "repository", "tree"],
    metadata={"tool_type": "github_api"},
)
@log_function_call(logger)
def get_github_repo_tree(github_url: str, branch: str = "main"):
    """Get the work tree structure of a GitHub repository using GitHub API.

    Args:
        github_url (str): The GitHub repository URL (e.g., "https://github.com/owner/repo" or "owner/repo")
        branch (str): The branch name to get the tree from (default: "main")

    Examples:
        get_github_repo_tree("https://github.com/octocat/Hello-World")
        get_github_repo_tree("octocat/Hello-World", "develop")
        get_github_repo_tree("microsoft/vscode", "main")

    Returns:
        dict: Contains the repository tree structure with file paths and types
    """
    logger.info(f"Getting GitHub repository tree for: {github_url}")
    add_trace_metadata({"repo_url": github_url, "branch": branch})
    add_trace_tags(["github_tree", "repo_structure"])

    try:
        # Extract owner and repo from URL
        import re

        # Handle both full URLs and owner/repo format
        if github_url.startswith("http"):
            match = re.match(
                r"https://github\.com/([^/]+)/([^/]+)", github_url.rstrip("/")
            )
            if not match:
                raise ValueError("Invalid GitHub URL format")
            owner, repo = match.groups()
        else:
            # Assume format is "owner/repo"
            if "/" not in github_url:
                raise ValueError(
                    "Invalid repository format. Use 'owner/repo' or full URL"
                )
            owner, repo = github_url.split("/", 1)

        # Remove .git suffix if present
        repo = repo.replace(".git", "")

        logger.info(f"Parsed repository: {owner}/{repo}")
        add_trace_metadata({"owner": owner, "repo": repo})

        # GitHub API endpoint for getting repository tree
        api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"

        # Make request to GitHub API
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Tree-Fetcher",
        }

        logger.info("Making unauthenticated request to public repository")
        add_trace_tags(["public_repo"])

        response = requests.get(api_url, headers=headers, timeout=30)

        if response.status_code == 404:
            logger.error(f"Repository or branch not found: {owner}/{repo}@{branch}")
            add_trace_tags(["repo_not_found"])
            return {
                "success": False,
                "error": f"Repository or branch not found: {owner}/{repo}@{branch}",
                "status_code": 404,
            }
        elif response.status_code != 200:
            logger.error(
                f"GitHub API request failed with status {response.status_code}"
            )
            add_trace_tags(["api_error"])
            return {
                "success": False,
                "error": f"GitHub API request failed: {response.status_code} - {response.text}",
                "status_code": response.status_code,
            }

        tree_data = response.json()

        # Process tree data
        tree_items = []
        for item in tree_data.get("tree", []):
            tree_items.append(
                {
                    "path": item["path"],
                    "type": item["type"],  # "blob" for files, "tree" for directories
                    "sha": item["sha"],
                    "size": item.get("size"),
                    "url": item.get("url"),
                }
            )

        result = {
            "success": True,
            "repository": f"{owner}/{repo}",
            "branch": branch,
            "tree_sha": tree_data.get("sha"),
            "total_items": len(tree_items),
            "tree": tree_items,
        }

        logger.info(f"Successfully retrieved tree with {len(tree_items)} items")
        add_trace_metadata(
            {"tree_items_count": len(tree_items), "tree_sha": tree_data.get("sha")}
        )
        add_trace_tags(["tree_retrieved_successfully"])

        return result

    except Exception as e:
        logger.error(f"Failed to get GitHub repository tree: {str(e)}")
        add_trace_tags(["tree_fetch_failed"])
        add_trace_metadata({"error": str(e)})
        return {"success": False, "error": f"Failed to get repository tree: {str(e)}"}


@tool
@langsmith_trace(
    name="get_github_file_contents",
    run_type="tool",
    tags=["github", "api", "files", "content"],
    metadata={"tool_type": "github_api"},
)
@log_function_call(logger)
def get_github_file_contents(github_url: str, file_paths: list, branch: str = "main"):
    """Get the contents of one or more files from a GitHub repository using GitHub API.

    Args:
        github_url (str): The GitHub repository URL (e.g., "https://github.com/owner/repo" or "owner/repo")
        file_paths (list): List of file paths within the repository to retrieve
        branch (str): The branch name to get files from (default: "main")

    Examples:
        get_github_file_contents("https://github.com/octocat/Hello-World", ["README.md"])
        get_github_file_contents("octocat/Hello-World", ["src/main.py", "config/settings.json"])
        get_github_file_contents("microsoft/vscode", ["package.json", "src/vs/code/electron-main/main.ts"], "main")
        get_github_file_contents("facebook/react", ["packages/react/index.js", "packages/react-dom/index.js"])

    Returns:
        dict: Contains the file contents and metadata for each requested file
    """
    logger.info(
        f"Getting GitHub file contents for {len(file_paths)} files from: {github_url}"
    )
    add_trace_metadata(
        {
            "repo_url": github_url,
            "branch": branch,
            "file_count": len(file_paths),
            "files": file_paths,
        }
    )
    add_trace_tags(["github_files", "content_fetch"])

    try:
        # Extract owner and repo from URL
        import re
        import base64

        # Handle both full URLs and owner/repo format
        if github_url.startswith("http"):
            match = re.match(
                r"https://github\.com/([^/]+)/([^/]+)", github_url.rstrip("/")
            )
            if not match:
                raise ValueError("Invalid GitHub URL format")
            owner, repo = match.groups()
        else:
            # Assume format is "owner/repo"
            if "/" not in github_url:
                raise ValueError(
                    "Invalid repository format. Use 'owner/repo' or full URL"
                )
            owner, repo = github_url.split("/", 1)

        # Remove .git suffix if present
        repo = repo.replace(".git", "")

        logger.info(f"Parsed repository: {owner}/{repo}")
        add_trace_metadata({"owner": owner, "repo": repo})

        # Prepare headers for GitHub API
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-File-Fetcher",
        }

        logger.info("Making unauthenticated request to public repository")
        add_trace_tags(["public_repo"])

        files_data = []
        errors = []

        for file_path in file_paths:
            logger.info(f"Fetching file: {file_path}")

            # GitHub API endpoint for getting file contents
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"

            try:
                response = requests.get(api_url, headers=headers, timeout=30)

                if response.status_code == 404:
                    error_msg = f"File not found: {file_path}"
                    logger.warning(error_msg)
                    errors.append(
                        {"file": file_path, "error": error_msg, "status_code": 404}
                    )
                    continue
                elif response.status_code != 200:
                    error_msg = (
                        f"API request failed for {file_path}: {response.status_code}"
                    )
                    logger.error(error_msg)
                    errors.append(
                        {
                            "file": file_path,
                            "error": error_msg,
                            "status_code": response.status_code,
                        }
                    )
                    continue

                file_data = response.json()

                # Decode file content if it's base64 encoded
                content = ""
                if file_data.get("encoding") == "base64":
                    try:
                        content = base64.b64decode(file_data["content"]).decode("utf-8")
                    except UnicodeDecodeError:
                        # File might be binary
                        content = f"[Binary file - {file_data.get('size', 0)} bytes]"
                        logger.info(f"File {file_path} appears to be binary")
                else:
                    content = file_data.get("content", "")

                files_data.append(
                    {
                        "path": file_path,
                        "content": content,
                        "size": file_data.get("size"),
                        "sha": file_data.get("sha"),
                        "type": file_data.get("type"),
                        "encoding": file_data.get("encoding"),
                        "download_url": file_data.get("download_url"),
                    }
                )

                logger.info(
                    f"Successfully retrieved file: {file_path} ({file_data.get('size', 0)} bytes)"
                )

            except requests.RequestException as e:
                error_msg = f"Request failed for {file_path}: {str(e)}"
                logger.error(error_msg)
                errors.append({"file": file_path, "error": error_msg})

        result = {
            "success": len(files_data) > 0 or len(errors) == 0,
            "repository": f"{owner}/{repo}",
            "branch": branch,
            "files_retrieved": len(files_data),
            "files_requested": len(file_paths),
            "files": files_data,
            "errors": errors,
        }

        logger.info(
            f"File retrieval completed: {len(files_data)} successful, {len(errors)} errors"
        )
        add_trace_metadata(
            {
                "files_retrieved": len(files_data),
                "files_with_errors": len(errors),
                "total_requested": len(file_paths),
            }
        )

        if len(files_data) > 0:
            add_trace_tags(["files_retrieved_successfully"])
        if len(errors) > 0:
            add_trace_tags(["some_files_failed"])

        return result

    except Exception as e:
        logger.error(f"Failed to get GitHub file contents: {str(e)}")
        add_trace_tags(["file_fetch_failed"])
        add_trace_metadata({"error": str(e)})
        return {"success": False, "error": f"Failed to get file contents: {str(e)}"}
