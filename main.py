from utils.logger import setup_logger, log_function_call
from utils.langsmith_utils import langsmith_trace, add_trace_tags, add_trace_metadata

logger = setup_logger(__name__)


@langsmith_trace(
    name="main_application",
    run_type="chain",
    tags=["application", "startup", "main"],
    metadata={"component": "main_application"},
)
@log_function_call(logger)
def main():
    logger.info("Application starting...")
    add_trace_tags(["app_startup"])
    add_trace_metadata({"application_name": "bajaj-hackrx-finals"})

    print("Hello from bajaj-hackrx-finals!")

    logger.info("Application finished successfully")
    add_trace_tags(["app_completed"])


if __name__ == "__main__":
    logger.info("Script started directly")
    add_trace_tags(["direct_execution"])
    main()
    logger.info("Script completed")
