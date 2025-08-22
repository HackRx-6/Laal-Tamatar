from pydantic import BaseModel, HttpUrl
from typing import List
from .logger import setup_logger

logger = setup_logger(__name__)

logger.info("Models module initialized")


class ChallengeRequest(BaseModel):
    url: HttpUrl
    questions: List[str]
    
    def __init__(self, **data):
        logger.info(f"Creating ChallengeRequest with data: {data}")
        super().__init__(**data)
        logger.info(f"ChallengeRequest created successfully with {len(self.questions)} questions")


class ChallengeResponse(BaseModel):
    answers: List[str]
    
    def __init__(self, **data):
        logger.info(f"Creating ChallengeResponse with {len(data.get('answers', []))} answers")
        super().__init__(**data)
        logger.info("ChallengeResponse created successfully")
