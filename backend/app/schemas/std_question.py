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
    tags: Optional[List[str]] = None  # 添加标签支持

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
    tags: Optional[List[str]] = None  # 添加 tags 字段
    
    class Config:        
        from_attributes = True
    
    @classmethod
    def from_db_model(cls, db_obj):
        """从数据库对象创建响应模型"""
        # 转换基本字段
        data = {
            'id': db_obj.id,
            'body': db_obj.body,
            'question_type': db_obj.question_type,
            'dataset_id': db_obj.dataset_id,
            'is_valid': db_obj.is_valid,
            'created_at': db_obj.created_at,
            'previous_version_id': db_obj.previous_version_id,
        }
        
        # 转换标签
        if hasattr(db_obj, 'tags') and db_obj.tags:
            data['tags'] = [tag.label for tag in db_obj.tags]
        else:
            data['tags'] = []
        
        # 转换数据集信息
        if hasattr(db_obj, 'dataset') and db_obj.dataset:
            data['dataset'] = {
                'id': db_obj.dataset.id,
                'name': db_obj.dataset.name,
                'description': db_obj.dataset.description,
            }
        else:
            data['dataset'] = None
        
        # 暂时不处理 std_answers，避免循环引用
        data['std_answers'] = None
        
        return cls(**data)
