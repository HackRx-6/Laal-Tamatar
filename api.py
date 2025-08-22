from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from utils.agent import get_answers
import time
from utils.models import ChallengeRequest, ChallengeResponse
app = FastAPI(
    title="Team Laal Tamatar's API !",
    description="welcome to our api :)",
    version="1.0.0",
)

@app.get("/")
async def root():
    return {
        "message": "Laal Tamatar's API",
        "description": "Send POST requests to /run.",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time(), "service": "laal-tamatar-api"}


@app.post('/run', response_model=ChallengeResponse)
async def run(request: ChallengeRequest):
    try:

        response = get_answers(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
