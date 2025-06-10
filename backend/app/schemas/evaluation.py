"""
Evaluation schemas for API serialization
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from enum import Enum


class EvaluatorType(str, Enum):
    """评估者类型"""
    USER = "user"
    LLM = "llm"


class EvaluationBase(BaseModel):
    """评估基础schema"""
    std_question_id: int
    llm_answer_id: int
    score: int  # 0-100分
    evaluator_type: EvaluatorType
    evaluator_id: Optional[int] = None  # 自动评估时为None
    evaluation_criteria: Optional[str] = None
    feedback: Optional[str] = None


class EvaluationCreate(EvaluationBase):
    """创建评估的schema"""
    pass


class EvaluationUpdate(BaseModel):
    """更新评估的schema"""
    score: Optional[int] = None
    feedback: Optional[str] = None
    evaluation_criteria: Optional[str] = None
    is_valid: Optional[bool] = None


class EvaluationResponse(EvaluationBase):
    """评估响应schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    is_valid: bool


class BatchEvaluationRequest(BaseModel):
    """批量评估请求schema"""
    llm_answer_ids: List[int]
    evaluation_type: str  # "auto" or "manual"
    evaluation_criteria: Optional[str] = None


class EvaluationStatistics(BaseModel):
    """评估统计schema"""
    total_evaluations: int
    average_score: float
    user_evaluations: int
    auto_evaluations: int
    score_distribution: dict