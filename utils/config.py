import logging
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

LOGGING_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

DEFAULT_LOG_LEVEL = LOGGING_LEVELS.get(LOG_LEVEL, logging.INFO)

LOG_FUNCTION_CALLS = os.getenv("LOG_FUNCTION_CALLS", "true").lower() == "true"
LOG_REQUESTS_RESPONSES = os.getenv("LOG_REQUESTS_RESPONSES", "true").lower() == "true"
LOG_HTTP_MIDDLEWARE = os.getenv("LOG_HTTP_MIDDLEWARE", "true").lower() == "true"

LOG_FORMAT = os.getenv(
    "LOG_FORMAT", 
    "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
)

print(f"Logging configuration loaded:")
print(f"  - Log Level: {LOG_LEVEL}")
print(f"  - Function Calls: {LOG_FUNCTION_CALLS}")
print(f"  - Requests/Responses: {LOG_REQUESTS_RESPONSES}")
print(f"  - HTTP Middleware: {LOG_HTTP_MIDDLEWARE}")
