from utils.logger import setup_logger, log_function_call

logger = setup_logger(__name__)

@log_function_call(logger)
def main():
    logger.info("Application starting...")
    print("Hello from bajaj-hackrx-finals!")
    logger.info("Application finished successfully")


if __name__ == "__main__":
    logger.info("Script started directly")
    main()
    logger.info("Script completed")
