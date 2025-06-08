from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class StdAnswerScoringPointBase(BaseModel):
    answer: str
    point_order: Optional[int] = 0

class StdAnswerScoringPointCreate(StdAnswerScoringPointBase):
    pass

class StdAnswerScoringPoint(StdAnswerScoringPointBase):
    id: int
    std_answer_id: int
    is_valid: bool
    previous_version_id: Optional[int] = None

    class Config:
        from_attributes = True

class StdAnswerBase(BaseModel):
    answer: str
    answered_by: Optional[int] = None  # 统一为answered_by，并改为int类型用户ID

class StdAnswerCreate(StdAnswerBase):
    std_question_id: Optional[int] = None  # 在嵌套创建时不需要，在独立创建时需要
    version: Optional[int] = None
    previous_version_id: Optional[int] = None
    scoring_points: List[StdAnswerScoringPointCreate] = []
    referenced_raw_answer_ids: List[int] = []
    referenced_expert_answer_ids: List[int] = []

class StdAnswerUpdate(BaseModel):
    answer: Optional[str] = None
    answered_by: Optional[int] = None  # 统一为answered_by
    previous_version_id: Optional[int] = None
    scoring_points: Optional[List[StdAnswerScoringPointCreate]] = None
    referenced_raw_answer_ids: Optional[List[int]] = None
    referenced_expert_answer_ids: Optional[List[int]] = None

class StdAnswer(StdAnswerBase):
    id: int
    std_question_id: int
    is_valid: bool
    answered_at: datetime  # 统一为answered_at
    previous_version_id: Optional[int] = None

    class Config:
        from_attributes = True

class StdAnswerWithScoringPoints(StdAnswer):
    scoring_points: List[StdAnswerScoringPoint] = []

    class Config:
        from_attributes = True


# 添加缺失的响应类
class StdAnswerScoringPointResponse(StdAnswerScoringPoint):
    """标准答案评分点响应模型"""
    class Config:
        from_attributes = True

class StdAnswerResponse(StdAnswerWithScoringPoints):
    """标准答案响应模型"""
    class Config:
        from_attributes = True
