import regex


def extract_json(str):
    # Returns the JSON object extracted from the string
    # Try to extract from ``` ```, ```json ```
    pass


def remove_script_tags(str):
    return regex.sub(
        r"<script.*?>.*?</script>", "", str, flags=regex.IGNORECASE | regex.DOTALL
    )[:10000]
