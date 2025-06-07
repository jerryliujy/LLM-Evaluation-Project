"""
Evaluation schemas for API serialization
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from enum import Enum


class EvaluatorType(str, Enum):
    """评估者类型"""
    USER = "user"
    LLM = "llm"


class EvaluationBase(BaseModel):
    """评估基础schema"""
    std_answer_id: int
    evaluator_type: EvaluatorType
    evaluator_id: Optional[int] = None  # LLM评估时为None
    score: int
    feedback: Optional[str] = None
    evaluation_criteria: Optional[str] = None


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