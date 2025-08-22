import os
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from .logger import setup_logger, log_function_call

load_dotenv()

logger = setup_logger(__name__)


@log_function_call(logger)
def get_llm(model: str, mode: str):
    logger.info(f"Creating LLM instance with model: {model}")
    if mode == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_ENDPOINT")

        logger.info(f"Using API endpoint: {base_url}")
        logger.info(f"API key configured: {'Yes' if api_key else 'No'}")

        llm = ChatOpenAI(
            api_key=api_key,  # type:ignore
            base_url=base_url,
            model=model,
        )

        logger.info(f"Successfully created LLM instance for model: {model}")
        return llm
    if mode == "azure":
        #         AZURE_OPENAI_API_KEY=7MMmELupHc7gW6DGAAQBfPs4H5CEwP856EZmOpEzUJGwhVeMMMeIJQQJ99BDACYeBjFXJ3w3AAABACOGpMkI
        # AZURE_OPENAI_DEPLOYMENT="gpt-4o"
        # OPENAI_API_VERSION=2025-01-01-preview
        # AZURE_OPENAI_ENDPOINT=https://internaluse.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        base_url = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")

        logger.info(f"Using API endpoint: {base_url}")
        logger.info(f"API key configured: {'Yes' if api_key else 'No'}")
        logger.info(f"Deployment name: {deployment_name}")

        llm = AzureChatOpenAI(
            api_key=api_key,  # type:ignore
            azure_endpoint=base_url,
            azure_deployment=deployment_name,
            # model=model,
        )

        logger.info(f"Successfully created LLM instance for model: {model}")
        return llm
