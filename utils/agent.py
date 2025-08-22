from langgraph.prebuilt import create_react_agent
from utils.tools import make_curl_request, execute_python_code, git_commit_and_push
from utils.llms import get_llm
from langchain_core.messages import SystemMessage
from utils.prompts import AGENT_SYSTEM_PROMPT
from utils.models import ChallengeRequest, ChallengeResponse
from .logger import setup_logger, log_function_call, log_request_response
from .langsmith_utils import langsmith_trace, add_trace_tags, add_trace_metadata
from dotenv import load_dotenv
import os

load_dotenv(override=True)
logger = setup_logger(__name__)

logger.info("Initializing agent...")
agent = create_react_agent(
    model=get_llm(os.getenv("MODEL_NAME"), os.getenv("ENDPOINT_TYPE")),
    tools=[make_curl_request, execute_python_code, git_commit_and_push],
)
logger.info("Agent initialized successfully")


@langsmith_trace(
    name="get_answers",
    run_type="chain",
    tags=["agent", "challenge", "main_entry_point"],
    metadata={"component": "challenge_processor"},
)
@log_request_response(logger)
def get_answers(challenge_request: ChallengeRequest) -> ChallengeResponse:
    logger.info(
        f"Processing challenge request with {len(challenge_request.questions)} questions"
    )
    logger.info(f"Target URL: {str(challenge_request.url)}")

    # Add trace metadata for the request
    add_trace_metadata(
        {
            "num_questions": len(challenge_request.questions),
            "target_url": str(challenge_request.url),
            "query": str(challenge_request.query),
            "request_id": id(challenge_request),
        }
    )
    add_trace_tags(["challenge_processing", "multi_question"])

    answers = []
    for i, question in enumerate(challenge_request.questions, 1):
        logger.info(
            f"Processing question {i}/{len(challenge_request.questions)}: {question}"
        )

        # Add tags for current question processing
        add_trace_tags([f"question_{i}", f"total_{len(challenge_request.questions)}"])

        # Create a copy of challenge_request without the 'questions' field for context
        context_data = challenge_request.model_dump(exclude={"questions"})
        normal_prompt = (
            f"Question: {question}\n\n"
            f"You are an expert assistant. Please answer the following question as thoroughly and accurately as possible, using the provided context. "
            f"Be detailed, clear, and ensure your answer is helpful and relevant to the question. "
            f"If the context does not contain enough information, use your best judgment to provide a useful answer, but indicate any assumptions you make.\n\n"
            f"Provided Context:\n{str(context_data)}\n\n"
        )
        logger.info(f"Generated prompt for question {i}: {normal_prompt}")

        try:
            response = process_single_question(
                question=question,
                prompt=normal_prompt,
                question_index=i,
                total_questions=len(challenge_request.questions),
            )
            answers.append(response)
            logger.info(f"Successfully processed question {i}")
        except Exception as e:
            logger.error(f"Failed to process question {i}: {str(e)}")
            add_trace_tags(["error", f"question_{i}_failed"])
            add_trace_metadata({"error": str(e), "failed_question_index": i})
            raise

    logger.info(f"Successfully processed all {len(answers)} questions")
    add_trace_metadata({"total_answers_generated": len(answers)})
    add_trace_tags(["completed_successfully"])
    return ChallengeResponse(answers=answers)


@langsmith_trace(
    name="process_single_question",
    run_type="chain",
    tags=["agent", "single_question"],
    metadata={"component": "question_processor"},
)
def process_single_question(
    question: str,
    prompt: str,
    question_index: int,
    total_questions: int,
) -> str:
    """Process a single question with LangSmith tracing"""
    logger.info(f"Processing question {question_index}/{total_questions}")

    # Add specific metadata for this question
    add_trace_metadata(
        {
            "question": question,
            "question_index": question_index,
            "total_questions": total_questions,
        }
    )
    add_trace_tags([f"question_index_{question_index}", "single_question_processing"])

    try:
        messages = [SystemMessage(AGENT_SYSTEM_PROMPT)]
        messages.append(prompt)
        response = agent.invoke({"messages": messages})
        logger.info(f"Agent response for question {question_index}: {response}")

        result = response["messages"][-1].content
        add_trace_metadata({"response_length": len(result)})
        add_trace_tags(["question_completed"])

        return result
    except Exception as e:
        logger.error(f"Failed to process question {question_index}: {str(e)}")
        add_trace_tags(["question_failed"])
        add_trace_metadata({"error_details": str(e)})
        raise
