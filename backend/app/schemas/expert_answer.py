from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ExpertAnswerBase(BaseModel):
    content: str

class ExpertAnswerCreate(ExpertAnswerBase):
    question_id: int 
    author: int

class ExpertAnswerUpdate(BaseModel):
    content: Optional[str] = None

class ExpertAnswer(ExpertAnswerBase):
    id: int
    question_id: int
    author: int
    created_at: datetime
    is_deleted: bool
    referenced_by_std_answer_id: Optional[int] = None

    class Config:
        from_attributes = True