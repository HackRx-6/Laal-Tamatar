from langgraph.prebuilt import create_react_agent
from utils.tools import (
    make_curl_request,
    execute_python_code,
    git_commit_and_push,
    get_github_repo_tree,
    get_github_file_contents,
)
from .parsers import extract_json
from utils.llms import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from utils.prompts import AGENT_SYSTEM_PROMPT
from utils.models import ChallengeRequest, ChallengeResponse
from .logger import setup_logger, log_request_response
from .langsmith_utils import langsmith_trace, add_trace_tags, add_trace_metadata
from dotenv import load_dotenv
import os

load_dotenv(override=True)
print(os.getenv("MODEL_NAME"))
logger = setup_logger(__name__)

logger.info("Initializing agent...")
agent = create_react_agent(
    model=get_llm(os.getenv("MODEL_NAME"), os.getenv("ENDPOINT_TYPE")),
    tools=[
        make_curl_request,
        execute_python_code,
        git_commit_and_push,
        get_github_repo_tree,
        get_github_file_contents,
    ],
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

    # Configuration variable to control processing methodology
    USE_MULTIPLE_QUESTIONS_MODE = (
        os.getenv("USE_MULTIPLE_QUESTIONS_MODE", "true").lower() == "true"
    )

    # Add trace metadata for the request
    add_trace_metadata(
        {
            "num_questions": len(challenge_request.questions),
            "target_url": str(challenge_request.url),
            "query": str(challenge_request.query),
            "request_id": id(challenge_request),
            "processing_mode": "multiple" if USE_MULTIPLE_QUESTIONS_MODE else "single",
        }
    )
    add_trace_tags(
        [
            "challenge_processing",
            "multi_question" if USE_MULTIPLE_QUESTIONS_MODE else "single_question",
        ]
    )

    # Create a copy of challenge_request without the 'questions' field for context
    context_data = challenge_request.model_dump(exclude={"questions"})

    if USE_MULTIPLE_QUESTIONS_MODE:
        # Process all questions at once
        logger.info("Using multiple questions processing mode")
        multiple_questions_prompt = (
            f"You are an expert assistant. Please answer the following questions as thoroughly and accurately as possible, using the provided context. "
            f"Be detailed, clear, and ensure your answers are helpful and relevant to the questions. "
            f"If the context does not contain enough information, use your best judgment to provide useful answers, but indicate any assumptions you make.\n\n"
            f"Provided Context:\n{str(context_data)}\n\n"
            f"Questions_data: {str(challenge_request.questions)}"
        )

        try:
            answers = process_multiple_questions(
                questions=challenge_request.questions,
                prompt=multiple_questions_prompt,
                total_questions=len(challenge_request.questions),
            )
            logger.info("Successfully processed all questions in multiple mode")
        except Exception as e:
            logger.error(f"Failed to process questions in multiple mode: {str(e)}")
            add_trace_tags(["error", "multiple_mode_failed"])
            add_trace_metadata({"error": str(e)})
            raise
    else:
        # Process questions one by one
        logger.info("Using single question processing mode")
        answers = []
        for i, question in enumerate(challenge_request.questions, 1):
            logger.info(
                f"Processing question {i}/{len(challenge_request.questions)}: {question}"
            )

            # Add tags for current question processing
            add_trace_tags(
                [f"question_{i}", f"total_{len(challenge_request.questions)}"]
            )

            single_question_prompt = (
                f"Question: {question}\n\n"
                f"You are an expert assistant. Please answer the following question as thoroughly and accurately as possible, using the provided context. "
                f"Be detailed, clear, and ensure your answer is helpful and relevant to the question. "
                f"If the context does not contain enough information, use your best judgment to provide a useful answer, but indicate any assumptions you make.\n\n"
                f"Provided Context:\n{str(context_data)}\n\n"
            )

            logger.info(f"Generated prompt for question {i}: {single_question_prompt}")

            try:
                response = process_single_question(
                    question=question,
                    prompt=single_question_prompt,
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

    logger.info(
        f"Successfully processed all questions. Total answers: {len(answers) if isinstance(answers, list) else 'response array'}"
    )
    add_trace_metadata(
        {
            "total_answers_generated": len(answers)
            if isinstance(answers, list)
            else "response_array"
        }
    )
    add_trace_tags(["completed_successfully"])
    return ChallengeResponse(answers=answers)


@langsmith_trace(
    name="process_multiple_questions",
    run_type="chain",
    tags=["agent", "multiple_questions"],
    metadata={"component": "question_processor"},
)
def process_multiple_questions(
    questions: str,
    prompt: str,
    total_questions: int,
):
    """Process multiple questions with LangSmith tracing - returns the response array directly"""
    logger.info(f"Processing multiple questions {total_questions}")

    # Add specific metadata for this question
    add_trace_metadata(
        {
            "questions": questions,
            "total_questions": total_questions,
        }
    )
    add_trace_tags(["multiple_questions_processing"])

    try:
        messages = [SystemMessage(AGENT_SYSTEM_PROMPT)]
        messages.append(HumanMessage(prompt))
        response = agent.invoke({"messages": messages})
        logger.info(f"Agent response for questions: {response}")

        result = response["messages"][-1].content

        # Extract JSON and return the array directly for multiple questions mode
        answers = extract_json(result)
        add_trace_metadata(
            {"response_length": len(result), "answers_type": type(answers).__name__}
        )
        add_trace_tags(["question_completed"])

        # Return the extracted answers array directly
        return answers
    except Exception as e:
        logger.error(f"Failed to process questions: {str(e)}")
        add_trace_tags(["question_failed"])
        add_trace_metadata({"error_details": str(e)})
        raise


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
        messages.append(SystemMessage(prompt))
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
