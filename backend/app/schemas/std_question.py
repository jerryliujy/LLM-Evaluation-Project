from pydantic import BaseModel
from typing import Optional, List, TYPE_CHECKING, ForwardRef
from datetime import datetime

if TYPE_CHECKING:
    from .tag import TagResponse

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
    # 移除tags字段避免循环导入

    class Config:
        from_attributes = True

# 添加response模型的别名
StdQuestionResponse = StdQuestionWithDetails
