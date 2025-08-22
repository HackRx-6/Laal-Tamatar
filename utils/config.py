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
    "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
)

# LangSmith Configuration
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "hackrx-bajaj")

print("Logging configuration loaded:")
print(f"  - Log Level: {LOG_LEVEL}")
print(f"  - Function Calls: {LOG_FUNCTION_CALLS}")
print(f"  - Requests/Responses: {LOG_REQUESTS_RESPONSES}")
print(f"  - HTTP Middleware: {LOG_HTTP_MIDDLEWARE}")
print(f"  - LangSmith Tracing: {LANGSMITH_TRACING}")
print(f"  - LangSmith Project: {LANGSMITH_PROJECT}")
