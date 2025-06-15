from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel
from datetime import datetime

if TYPE_CHECKING:
    from .std_answer import StdAnswerResponse

class StdQuestionBase(BaseModel):
    dataset_id: int  # 当前所在的数据集ID
    body: str  # 使用body字段而不是text
    question_type: str
    is_valid: bool = True
    created_by: Optional[str] = None 
    version: int = 1
    previous_version_id: Optional[int] = None
    original_version_id: Optional[int] = None  # 最初创建时的版本ID
    current_version_id: Optional[int] = None  # 当前所在的版本ID

class StdQuestionCreate(StdQuestionBase):
    tags: Optional[List[str]] = []  # 创建时使用标签名称列表

class StdQuestionUpdate(BaseModel):
    dataset_id: Optional[int] = None
    body: Optional[str] = None  # 使用body字段而不是text
    question_type: Optional[str] = None
    is_valid: Optional[bool] = None
    # 明确排除用户相关和版本管理字段，这些在普通编辑时不应被修改
    # created_by, version, previous_version_id, original_version_id, current_version_id 等字段不包含在这里
    tags: Optional[List[str]] = None  # 标签列表，可选更新

class StdQuestionResponse(StdQuestionBase):
    id: int
    created_at: datetime  # 使用created_at字段而不是create_time
    tags: List[str] = []  # 返回标签名称列表
    dataset: Optional[dict] = None  # 添加数据集信息支持
    std_answers: Optional[List[dict]] = None  # 添加关联的标准答案列表
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_db_model(cls, db_obj):
        """从数据库对象创建响应对象，确保正确的数据转换"""
        return cls(
            id=db_obj.id,
            dataset_id=db_obj.dataset_id,
            body=db_obj.body,
            question_type=db_obj.question_type,
            is_valid=db_obj.is_valid,
            created_by=db_obj.created_by_user.username if db_obj.created_by_user else "unknown",
            created_at=db_obj.created_at,
            version=db_obj.version,
            previous_version_id=db_obj.previous_version_id,
            original_version_id=db_obj.original_version_id,
            current_version_id=db_obj.current_version_id,
            tags=[tag.label for tag in db_obj.tags] if db_obj.tags else [],
            dataset={
                "id": db_obj.dataset.id,
                "name": db_obj.dataset.name,
                "description": db_obj.dataset.description,
                "version": db_obj.dataset.version  
            } if db_obj.dataset else None
        )

class StdQuestionInDB(StdQuestionBase):
    id: int
    created_at: datetime  # 使用created_at字段而不是create_time
    tags: List[str] = []  # 返回标签名称列表
    
    class Config:
        from_attributes = True
