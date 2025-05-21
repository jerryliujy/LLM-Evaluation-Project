from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RawAnswerBase(BaseModel):
    content: str
    vote_count: Optional[int] = 0
    author: Optional[str] = None
    answered_at: Optional[datetime] = None

class RawAnswerCreate(RawAnswerBase):
    question_id: int # Required when creating

class RawAnswer(RawAnswerBase):
    id: int
    question_id: int
    is_deleted: bool

    class Config:
        orm_mode = True # Pydantic V1, or from_attributes = True for V2