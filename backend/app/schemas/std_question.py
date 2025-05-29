from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class StdQuestionBase(BaseModel):
    dataset_id: int
    raw_question_id: int
    text: str
    question_type: str
    created_by: Optional[str] = None

class StdQuestionCreate(StdQuestionBase):
    pass

class StdQuestionUpdate(BaseModel):
    text: Optional[str] = None
    question_type: Optional[str] = None
    created_by: Optional[str] = None

class StdQuestion(StdQuestionBase):
    id: int
    create_time: datetime
    is_valid: bool
    version: int
    previous_version_id: Optional[int] = None

    class Config:
        from_attributes = True

class StdQuestionWithDetails(StdQuestion):
    dataset: Optional[dict] = None
    raw_question: Optional[dict] = None
    std_answers: List[dict] = []

    class Config:
        from_attributes = True
