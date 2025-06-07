from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, TYPE_CHECKING, ForwardRef, Any
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
    tags: List[str] = Field(default_factory=list)  # 输出为字符串列表

    @model_validator(mode='before')
    @classmethod
    def extract_tags(cls, data: Any) -> Any:
        """将Tag对象转换为标签名字符串列表"""
        if isinstance(data, dict):
            return data
            
        # 处理SQLAlchemy模型对象
        result = {}
        for field_name, field_value in data.__dict__.items():
            if field_name.startswith('_'):
                continue
            result[field_name] = field_value
            
        # 处理tags关系
        if hasattr(data, 'tags') and data.tags:
            result['tags'] = [tag.label for tag in data.tags]
        elif hasattr(data, 'tags_json') and data.tags_json:
            result['tags'] = data.tags_json
        else:
            result['tags'] = []
            
        return result

    class Config:
        from_attributes = True

# 添加response模型的别名
RawQuestionResponse = RawQuestion

# 组合创建模式
class RawAnswerCreateForQuestion(BaseModel):
    """用于在创建问题时一起创建答案的简化模式"""
    answer: str
    answered_by: Optional[str] = None
    upvotes: Optional[str] = "0"
    answered_at: Optional[datetime] = None

class RawQuestionWithAnswersCreate(BaseModel):
    """用于事务性创建问题和回答的模式"""
    question: RawQuestionCreate
    answers: List[RawAnswerCreateForQuestion] = []

class RawQuestionWithAnswersResponse(BaseModel):
    """返回创建结果的模式"""
    question: RawQuestion
    answers: List[RawAnswerSchema]
    success: bool = True
    message: Optional[str] = None