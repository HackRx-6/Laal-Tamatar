from langchain_core.tools import tool
import shlex
import requests
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
