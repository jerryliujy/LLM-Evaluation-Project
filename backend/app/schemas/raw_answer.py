from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class RawAnswerBase(BaseModel):
    answer: str  
    upvotes: Optional[str] = "0"  
    answered_by: Optional[str] = None  
    answered_at: Optional[datetime] = None

class RawAnswerCreate(RawAnswerBase):
    question_id: int # Required when creating

class RawAnswer(RawAnswerBase):
    id: int
    question_id: int
    created_by: Optional[int] = None
    is_deleted: bool

    class Config:
        from_attributes = True