from langgraph.prebuilt import create_react_agent
from utils.tools import make_curl_request
from utils.llms import get_llm
from langchain_core.messages import SystemMessage
from utils.prompts import AGENT_SYSTEM_PROMPT
from utils.models import ChallengeRequest, ChallengeResponse
from .logger import setup_logger, log_function_call, log_request_response

logger = setup_logger(__name__)

logger.info("Initializing agent...")
agent = create_react_agent(
    model=get_llm("gpt-5-nano", "openai"),
    tools=[make_curl_request],
)
logger.info("Agent initialized successfully")


@log_request_response(logger)
def get_answers(challenge_request: ChallengeRequest) -> ChallengeResponse:
    logger.info(
        f"Processing challenge request with {len(challenge_request.questions)} questions"
    )
    logger.info(f"Target URL: {challenge_request.url}")

    answers = []
    for i, question in enumerate(challenge_request.questions, 1):
        logger.info(
            f"Processing question {i}/{len(challenge_request.questions)}: {question}"
        )

        normal_prompt = f"Question: {question}\n\nURL: {challenge_request.url}\n\nAnswer the question based on the information from the URL."
        logger.info(f"Generated prompt for question {i}: {normal_prompt}")

        try:
            response = agent.invoke(
                {"messages": [SystemMessage(AGENT_SYSTEM_PROMPT), normal_prompt]}
            )
            logger.info(f"Agent response for question {i}: {response}")
            answers.append(response["messages"][-1].content)
            logger.info(f"Successfully processed question {i}")
        except Exception as e:
            logger.error(f"Failed to process question {i}: {str(e)}")
            raise

    logger.info(f"Successfully processed all {len(answers)} questions")
    return ChallengeResponse(answers=answers)
