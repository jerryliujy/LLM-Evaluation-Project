from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class StdQuestionBase(BaseModel):
    dataset_id: int
    body: str  # 统一字段名为body
    question_type: str
    created_by: Optional[int] = None  # 改为int类型用户ID

class StdQuestionCreate(StdQuestionBase):
    previous_version_id: Optional[int] = None

class StdQuestionUpdate(BaseModel):
    body: Optional[str] = None  # 统一字段名为body
    question_type: Optional[str] = None
    created_by: Optional[int] = None  # 改为int类型用户ID
    previous_version_id: Optional[int] = None

class StdQuestion(StdQuestionBase):
    id: int
    created_at: datetime  # 统一为created_at
    is_valid: bool
    previous_version_id: Optional[int] = None

    class Config:
        from_attributes = True

class StdQuestionResponse(StdQuestion):
    dataset: Optional[dict] = None
    std_answers: Optional[Any] = None  # 修正关系名称 
    class Config:        
        from_attributes = True
