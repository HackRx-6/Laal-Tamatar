import regex
from .logger import setup_logger, log_function_call

logger = setup_logger(__name__)


@log_function_call(logger)
def extract_json(str):
    logger.info(f"Attempting to extract JSON from string of length: {len(str)}")
    logger.debug(f"Input string preview: {str[:200]}...")
    
    logger.warning("JSON extraction not yet implemented")
    pass


@log_function_call(logger)
def remove_script_tags(str):
    logger.info(f"Removing script tags from string of length: {len(str)}")
    
    result = regex.sub(
        r"<script.*?>.*?</script>", "", str, flags=regex.IGNORECASE | regex.DOTALL
    )[:10000]
    
    logger.info(f"Script tags removed. Result length: {len(result)}")
    return result
