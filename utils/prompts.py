from .logger import setup_logger

logger = setup_logger(__name__)

logger.info("Prompts module initialized")

AGENT_SYSTEM_PROMPT = """
You are a helpful assistant. Your goal is to assist the user in finding information and answering questions to the best of your ability.
Use the tools available to you.
"""

logger.info("Agent system prompt loaded")
logger.debug(f"Agent system prompt: {AGENT_SYSTEM_PROMPT.strip()}")
