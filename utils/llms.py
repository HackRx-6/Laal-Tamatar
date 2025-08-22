import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from .logger import setup_logger, log_function_call

load_dotenv()

logger = setup_logger(__name__)

@log_function_call(logger)
def get_llm(model: str):
    logger.info(f"Creating LLM instance with model: {model}")
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    base_url = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    logger.info(f"Using API endpoint: {base_url}")
    logger.info(f"API key configured: {'Yes' if api_key else 'No'}")
    
    llm = ChatOpenAI(
        api_key=api_key, #type:ignore
        base_url=base_url,
        model=model
    )
    
    logger.info(f"Successfully created LLM instance for model: {model}")
    return llm