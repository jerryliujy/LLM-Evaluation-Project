from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ExpertAnswerBase(BaseModel):
    answer: str

class ExpertAnswerCreate(ExpertAnswerBase):
    question_id: int

class ExpertAnswerUpdate(BaseModel):
    answer: Optional[str] = None

class ExpertAnswer(ExpertAnswerBase):
    id: int
    question_id: int
    answered_by: int
    answered_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True