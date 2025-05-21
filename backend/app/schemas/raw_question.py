from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .raw_answer import RawAnswer as RawAnswerSchema
from .expert_answer import ExpertAnswer as ExpertAnswerSchema

class RawQuestionBase(BaseModel):
    title: str
    url: Optional[str] = None
    body: Optional[str] = None
    vote_count: Optional[int] = 0
    view_count: Optional[int] = 0
    author: Optional[str] = None
    tags: Optional[List[str]] = []
    issued_at: Optional[datetime] = None

class RawQuestionCreate(RawQuestionBase):
    pass

class RawQuestion(RawQuestionBase):
    id: int
    is_deleted: bool
    raw_answers: List[RawAnswerSchema] = []
    expert_answers: List[ExpertAnswerSchema] = []

    class Config:
        orm_mode = True