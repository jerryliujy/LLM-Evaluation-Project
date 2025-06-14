from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class StdQuestionBase(BaseModel):
    dataset_id: int  # 当前所在的数据集ID
    body: str  # 使用body字段而不是text
    question_type: str
    is_valid: bool = True
    created_by: Optional[str] = None  # 改为字符串类型，存储用户名
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
    created_by: Optional[str] = None
    version: Optional[int] = None
    previous_version_id: Optional[int] = None
    original_version_id: Optional[int] = None
    current_version_id: Optional[int] = None
    tags: Optional[List[str]] = None  # 标签列表，可选更新

class StdQuestionResponse(StdQuestionBase):
    id: int
    created_at: datetime  # 使用created_at字段而不是create_time
    tags: List[str] = []  # 返回标签名称列表
    
    class Config:
        from_attributes = True

class StdQuestionInDB(StdQuestionBase):
    id: int
    created_at: datetime  # 使用created_at字段而不是create_time
    tags: List[str] = []  # 返回标签名称列表
    
    class Config:
        from_attributes = True

# 兼容性字段映射
def std_question_to_dict(db_obj):
    """将数据库对象转换为字典，保持向后兼容"""
    return {
        'id': db_obj.id,
        'body': db_obj.body,  # 直接使用body字段
        'question_type': db_obj.question_type,
        'is_valid': db_obj.is_valid,
        'created_by': db_obj.created_by,
        'created_at': db_obj.created_at,  # 直接使用created_at字段
        'version': db_obj.version,
        'previous_version_id': db_obj.previous_version_id,
        'dataset_id': db_obj.dataset_id,
        'original_version_id': db_obj.original_version_id,
        'current_version_id': db_obj.current_version_id,
        'tags': [tag.label for tag in db_obj.tags] if db_obj.tags else [],  # 添加标签支持
    }
