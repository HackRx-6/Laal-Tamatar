from pydantic import BaseModel, HttpUrl
from typing import List


class ChallengeRequest(BaseModel):
    url: HttpUrl
    questions: List[str]


class ChallengeResponse(BaseModel):
    answers: List[str]
