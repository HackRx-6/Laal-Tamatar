from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from utils.agent import get_answers
import time
from utils.models import ChallengeRequest, ChallengeResponse
from utils.logger import setup_logger, log_request_response
from utils.langsmith_utils import langsmith_trace, add_trace_tags, add_trace_metadata
import uuid
from dotenv import load_dotenv
import json
import os
from datetime import datetime

load_dotenv(override=True)

logger = setup_logger(__name__)


def save_request_response(request_data: dict, response_data: dict):
    """Save request and response JSON to temp/requests.json file"""
    try:
        # Ensure temp directory exists
        os.makedirs("temp", exist_ok=True)

        # Prepare data with timestamp
        entry = {
            "timestamp": datetime.now().isoformat(),
            "request": request_data,
            "response": response_data,
        }

        # Read existing data or create new list
        requests_file = "temp/requests.json"
        if os.path.exists(requests_file):
            with open(requests_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

        # Append new entry
        data.append(entry)

        # Write back to file
        with open(requests_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved request/response to {requests_file}")
    except Exception as e:
        logger.error(f"Failed to save request/response: {str(e)}")


app = FastAPI(
    title="Team Laal Tamatar's API !",
    description="welcome to our api :)",
    version="1.0.0",
)

logger.info("FastAPI application initialized")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    logger.info(f"[{request_id}] {request.method} {request.url}")
    logger.info(f"[{request_id}] Headers: {dict(request.headers)}")
    logger.info(
        f"[{request_id}] Client: {request.client.host if request.client else 'Unknown'}"
    )

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(f"[{request_id}] Response status: {response.status_code}")
    logger.info(f"[{request_id}] Process time: {process_time:.4f}s")

    return response


@app.get("/")
@langsmith_trace(
    name="root_endpoint",
    run_type="chain",
    tags=["api", "endpoint", "health"],
    metadata={"endpoint": "/", "method": "GET"},
)
@log_request_response(logger)
async def root():
    logger.info("Root endpoint accessed")
    add_trace_tags(["root_access"])
    return {
        "message": "Laal Tamatar's API",
        "description": "Send POST requests to /run.",
    }


@app.get("/health")
@langsmith_trace(
    name="health_check",
    run_type="chain",
    tags=["api", "health", "monitoring"],
    metadata={"endpoint": "/health", "method": "GET"},
)
@log_request_response(logger)
async def health_check():
    logger.info("Health check endpoint accessed")
    timestamp = time.time()
    response = {
        "status": "healthy",
        "timestamp": timestamp,
        "service": "laal-tamatar-api",
    }
    logger.info(f"Health check response: {response}")
    add_trace_metadata({"health_status": "healthy", "response_timestamp": timestamp})
    add_trace_tags(["health_ok"])
    return response


@app.post("/run", response_model=ChallengeResponse)
@langsmith_trace(
    name="run_challenge_endpoint",
    run_type="chain",
    tags=["api", "challenge", "main_endpoint", "entry_point"],
    metadata={"endpoint": "/run", "method": "POST"},
)
@log_request_response(logger)
async def run(request: ChallengeRequest):
    logger.info("Run endpoint accessed")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Number of questions: {len(request.questions)}")

    # Convert request to dict for saving
    request_dict = request.model_dump()

    # Add comprehensive trace metadata for the main entry point
    add_trace_metadata(
        {
            "endpoint": "/run",
            "request_url": str(request.url),
            "questions_count": len(request.questions),
            "questions": request.questions,
            "request_type": "challenge_processing",
        }
    )
    add_trace_tags(
        ["main_entry_point", "challenge_api", f"questions_{len(request.questions)}"]
    )

    for i, question in enumerate(request.questions, 1):
        logger.info(f"Question {i}: {question}")

    try:
        logger.info("Starting to process challenge request")
        add_trace_tags(["processing_started"])

        response = get_answers(request)

        logger.info("Challenge request processed successfully")
        logger.info(f"Generated {len(response.answers)} answers")

        # Convert response to dict for saving
        response_dict = response.model_dump()

        # Save request and response to file
        save_request_response(request_dict, response_dict)

        # Add success metadata
        add_trace_metadata(
            {
                "processing_status": "success",
                "answers_generated": len(response.answers),
                "answers": response.answers,
            }
        )
        add_trace_tags(["processing_completed", "success"])

        return response

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")

        # Add error metadata to trace
        add_trace_metadata(
            {
                "processing_status": "failed",
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
        )
        add_trace_tags(["processing_failed", "error"])

        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
