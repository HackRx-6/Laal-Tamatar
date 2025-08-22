from langchain_core.tools import tool
import shlex
import requests


@tool
def make_curl_request(curl_request: str):
    """Use this endpoint to make curl requests.
    This returns a detailed response along wiht the headers and all.

    Args:
        curl_request (str): The complete and correct curl request
    """
    # Parse the curl command
    tokens = shlex.split(curl_request)
    if tokens[0].lower() != "curl":
        return {"error": "Not a valid curl command"}

    url = None
    method = "GET"
    headers = {}
    data = None
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token in ["-X", "--request"]:
            i += 1
            method = tokens[i].upper()
        elif token in ["-H", "--header"]:
            i += 1
            header = tokens[i]
            if ":" in header:
                k, v = header.split(":", 1)
                headers[k.strip()] = v.strip()
        elif token in ["-d", "--data", "--data-raw", "--data-binary", "--data-ascii"]:
            i += 1
            data = tokens[i]
            if method == "GET":
                method = "POST"
        elif token.startswith("http"):
            url = token
        i += 1

    if not url:
        return {"error": "No URL found in curl command"}

    try:
        response = requests.request(method, url, headers=headers, data=data)
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
        }
    except Exception as e:
        return {"error": str(e)}
