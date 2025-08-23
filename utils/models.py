from pydantic import BaseModel
from typing import List, Optional, Any
from .logger import setup_logger

logger = setup_logger(__name__)

logger.info("Models module initialized")


class ChallengeRequest(BaseModel):
    questions: List[str]  # Only required field
    url: Optional[str] = None  # Changed from HttpUrl to str to accept any text
    query: Optional[str] = None

    # Allow additional fields
    class Config:
        extra = "allow"  # This allows additional fields not explicitly defined

    def __init__(self, **data):
        logger.info(f"Creating ChallengeRequest with data: {data}")
        super().__init__(**data)
        logger.info(
            f"ChallengeRequest created successfully with {len(self.questions)} questions"
        )

        # Log any additional fields that were provided
        defined_fields = {"questions", "url", "query"}
        additional_fields = set(data.keys()) - defined_fields
        if additional_fields:
            logger.info(f"Additional fields provided: {additional_fields}")


class ChallengeResponse(BaseModel):
    answers: List[str]

    def __init__(self, **data):
        logger.info(
            f"Creating ChallengeResponse with {len(data.get('answers', []))} answers"
        )
        super().__init__(**data)
        logger.info("ChallengeResponse created successfully")
