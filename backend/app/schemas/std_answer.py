from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class StdAnswerScoringPointBase(BaseModel):
    scoring_point_text: str
    point_order: Optional[int] = 0
    created_by: Optional[str] = None

class StdAnswerScoringPointCreate(StdAnswerScoringPointBase):
    pass

class StdAnswerScoringPoint(StdAnswerScoringPointBase):
    id: int
    std_answer_id: int
    is_valid: bool
    create_time: datetime
    version: int
    previous_version_id: Optional[int] = None

    class Config:
        from_attributes = True

class StdAnswerBase(BaseModel):
    std_question_id: int
    answer: str
    created_by: Optional[str] = None

class StdAnswerCreate(StdAnswerBase):
    scoring_points: List[StdAnswerScoringPointCreate] = []

class StdAnswerUpdate(BaseModel):
    answer: Optional[str] = None
    created_by: Optional[str] = None
    scoring_points: Optional[List[StdAnswerScoringPointCreate]] = None

class StdAnswer(StdAnswerBase):
    id: int
    is_valid: bool
    create_time: datetime
    version: int
    previous_version_id: Optional[int] = None

    class Config:
        from_attributes = True

class StdAnswerWithDetails(StdAnswer):
    scoring_points: List[StdAnswerScoringPoint] = []

    class Config:
        from_attributes = True
