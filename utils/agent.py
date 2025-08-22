from langgraph.prebuilt import create_react_agent
from utils.tools import make_curl_request
from utils.llms import get_llm
from langchain_core.messages import SystemMessage
from utils.prompts import AGENT_SYSTEM_PROMPT
from utils.models import ChallengeRequest, ChallengeResponse


agent = create_react_agent(
    model=get_llm("gpt-5-nano"),
    tools=[make_curl_request],
)


def get_answers(challenge_request: ChallengeRequest) -> ChallengeResponse:
    # Use the agent to get answers for the questions in the challenge request
    # For every question, invoke the agent with the question
    answers = []
    for question in challenge_request.questions:
        normal_prompt = f"Question: {question}\n\nURL: {challenge_request.url}\n\nAnswer the question based on the information from the URL."
        response = agent.invoke([SystemMessage(AGENT_SYSTEM_PROMPT), normal_prompt])
        answers.append(response)
    return ChallengeResponse(answers=answers)
