from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ExpertAnswerBase(BaseModel):
    content: str
    source: str
    vote_count: Optional[int] = 0
    author: Optional[str] = None

class ExpertAnswerCreate(ExpertAnswerBase):
    question_id: int 
    expert_id: int

class ExpertAnswer(ExpertAnswerBase):
    id: int
    question_id: int
    created_at: datetime
    is_deleted: bool

    class Config:
        orm_mode = True