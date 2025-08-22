from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from utils.agent import get_answers
import time
from utils.models import ChallengeRequest, ChallengeResponse
from utils.logger import setup_logger, log_request_response
import uuid

logger = setup_logger(__name__)

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
@log_request_response(logger)
async def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Laal Tamatar's API",
        "description": "Send POST requests to /run.",
    }


@app.get("/health")
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
    return response


@app.post("/run", response_model=ChallengeResponse)
@log_request_response(logger)
async def run(request: ChallengeRequest):
    logger.info("Run endpoint accessed")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Number of questions: {len(request.questions)}")
    for i, question in enumerate(request.questions, 1):
        logger.info(f"Question {i}: {question}")

    try:
        logger.info("Starting to process challenge request")
        response = get_answers(request)
        logger.info("Challenge request processed successfully")
        logger.info(f"Generated {len(response.answers)} answers")

        return response

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
