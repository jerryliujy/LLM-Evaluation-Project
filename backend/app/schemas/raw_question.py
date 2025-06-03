from pydantic import BaseModel
from typing import Optional, List, TYPE_CHECKING, ForwardRef
from datetime import datetime
from .raw_answer import RawAnswer as RawAnswerSchema
from .expert_answer import ExpertAnswer as ExpertAnswerSchema

if TYPE_CHECKING:
    from .tag import TagResponse

class RawQuestionBase(BaseModel):
    title: str
    url: Optional[str] = None
    body: Optional[str] = None
    votes: Optional[str] = "0"  # 改为str类型匹配模型
    views: Optional[str] = None  # str类型支持"1.1m"格式
    author: Optional[str] = None
    tags_json: Optional[List[str]] = []  # JSON格式的tags，用于输入
    issued_at: Optional[datetime] = None

class RawQuestionCreate(RawQuestionBase):
    pass

class RawQuestion(RawQuestionBase):
    id: int
    is_deleted: bool
    created_at: datetime
    raw_answers: List[RawAnswerSchema] = []
    expert_answers: List[ExpertAnswerSchema] = []
    # 移除tags字段避免循环导入

    class Config:
        from_attributes = True

# 添加response模型的别名
RawQuestionResponse = RawQuestion