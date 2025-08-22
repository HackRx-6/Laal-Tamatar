import regex
import json
from .logger import setup_logger, log_function_call

logger = setup_logger(__name__)


@log_function_call(logger)
def extract_json(str):
    logger.info(f"Attempting to extract JSON from string of length: {len(str)}")
    logger.debug(f"Input string preview: {str[:200]}...")

    # Try to extract JSON from markdown code blocks first
    json_patterns = [
        # JSON in markdown code blocks with language specification
        r"```json\s*(.*?)\s*```",
        r"```javascript\s*(.*?)\s*```",
        r"```js\s*(.*?)\s*```",
        # JSON in markdown code blocks without language specification
        r"```\s*([\[\{].*?[\]\}])\s*```",
        # JSON wrapped in backticks
        r"`\s*([\[\{].*?[\]\}])\s*`",
        # JSON at the beginning/end of string with optional whitespace
        r"^\s*([\[\{].*?[\]\}])\s*$",
        # JSON anywhere in the string (greedy match for complete JSON)
        r"([\[\{](?:[^[\]{}]|[\[\{](?:[^[\]{}]|[\[\{][^[\]{}]*[\]\}])*[\]\}])*[\]\}])",
    ]

    for pattern in json_patterns:
        logger.debug(f"Trying pattern: {pattern}")
        matches = regex.findall(pattern, str, regex.DOTALL | regex.MULTILINE)

        for match in matches:
            try:
                # Clean up the match
                json_str = match.strip()
                logger.debug(f"Found potential JSON: {json_str[:100]}...")

                # Try to parse as JSON
                parsed_json = json.loads(json_str)
                logger.info("Successfully extracted and parsed JSON")
                return parsed_json

            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse JSON: {e}")
                continue

    # If no valid JSON found, try to find any dict/list-like structure
    logger.warning("No valid JSON found in standard patterns, trying fallback")

    # Fallback: look for anything that starts with { or [ and try to parse
    fallback_matches = regex.findall(r"([\[\{].*)", str, regex.DOTALL)
    for match in fallback_matches:
        # Try progressively shorter substrings from the start
        json_str = match.strip()
        for i in range(len(json_str), 0, -1):
            try:
                substr = json_str[:i].rstrip()
                if substr.endswith(("}", "]")):
                    parsed_json = json.loads(substr)
                    logger.info("Successfully extracted JSON using fallback method")
                    return parsed_json
            except json.JSONDecodeError:
                continue

    logger.error("Failed to extract valid JSON from input string")
    raise ValueError("No valid JSON found in the input string")


@log_function_call(logger)
def remove_script_tags(str):
    logger.info(f"Removing script tags from string of length: {len(str)}")

    result = regex.sub(
        r"<script.*?>.*?</script>", "", str, flags=regex.IGNORECASE | regex.DOTALL
    )[:10000]

    logger.info(f"Script tags removed. Result length: {len(result)}")
    return result
