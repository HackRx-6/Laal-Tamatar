import os
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from .logger import setup_logger, log_function_call
from .langsmith_utils import langsmith_trace, add_trace_tags, add_trace_metadata

load_dotenv()

logger = setup_logger(__name__)


@langsmith_trace(
    name="get_llm",
    run_type="llm",
    tags=["llm_initialization", "model_creation"],
    metadata={"component": "llm_factory"},
)
@log_function_call(logger)
def get_llm(model: str, mode: str):
    logger.info(f"Creating LLM instance with model: {model}")

    # Add trace metadata
    add_trace_metadata({"model_name": model, "mode": mode, "provider": mode})
    add_trace_tags([f"model_{model}", f"provider_{mode}"])

    if mode == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_ENDPOINT")

        logger.info(f"Using API endpoint: {base_url}")
        logger.info(f"API key configured: {'Yes' if api_key else 'No'}")

        # Add OpenAI specific metadata
        add_trace_metadata({"api_endpoint": base_url, "has_api_key": bool(api_key)})
        add_trace_tags(["openai_provider"])

        llm = ChatOpenAI(
            api_key=api_key,  # type:ignore
            base_url=base_url,
            model=model,
        )

        logger.info(f"Successfully created LLM instance for model: {model}")
        add_trace_tags(["llm_created_successfully"])
        return llm

    if mode == "azure":
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        base_url = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")

        logger.info(f"Using API endpoint: {base_url}")
        logger.info(f"API key configured: {'Yes' if api_key else 'No'}")
        logger.info(f"Deployment name: {deployment_name}")

        # Add Azure specific metadata
        add_trace_metadata(
            {
                "azure_endpoint": base_url,
                "deployment_name": deployment_name,
                "has_api_key": bool(api_key),
            }
        )
        add_trace_tags(["azure_provider"])

        llm = AzureChatOpenAI(
            api_key=api_key,  # type:ignore
            azure_endpoint=base_url,
            azure_deployment=deployment_name,
            # model=model,
        )

        logger.info(f"Successfully created LLM instance for model: {model}")
        add_trace_tags(["llm_created_successfully"])
        return llm
