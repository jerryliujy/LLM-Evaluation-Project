from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class StdAnswerBase(BaseModel):
    std_question_id: int
    answer: str
    is_valid: bool = True
    created_by: Optional[str] = None
    version: int = 1
    previous_version_id: Optional[int] = None

class StdAnswerCreate(StdAnswerBase):
    pass

class StdAnswerUpdate(BaseModel):
    std_question_id: Optional[int] = None
    answer: Optional[str] = None
    is_valid: Optional[bool] = None
    created_by: Optional[str] = None
    version: Optional[int] = None
    previous_version_id: Optional[int] = None

class StdAnswerResponse(StdAnswerBase):
    id: int
    answered_at: datetime  # 使用 answered_at 而不是 create_time
    answered_by: Optional[str] = None  # 添加 answered_by 字段
    
    class Config:
        from_attributes = True

class StdAnswerInDB(StdAnswerBase):
    id: int
    answered_at: datetime  # 使用 answered_at 而不是 create_time
    answered_by: Optional[str] = None  # 添加 answered_by 字段
    
    class Config:
        from_attributes = True

class StdAnswerScoringPointBase(BaseModel):
    std_answer_id: int
    answer: str  # 使用 answer 字段匹配模型的 @property
    point_order: int = 0
    is_valid: bool = True
    previous_version_id: Optional[int] = None

class StdAnswerScoringPointCreate(StdAnswerScoringPointBase):
    pass

class StdAnswerScoringPointUpdate(BaseModel):
    std_answer_id: Optional[int] = None
    answer: Optional[str] = None  # 使用 answer 字段匹配模型的 @property
    point_order: Optional[int] = None
    is_valid: Optional[bool] = None
    previous_version_id: Optional[int] = None

class StdAnswerScoringPointResponse(StdAnswerScoringPointBase):
    id: int
    # 移除 create_time 字段，因为 CRUD 返回的数据中没有这个字段
    
    class Config:
        from_attributes = True

class StdAnswerScoringPointInDB(StdAnswerScoringPointBase):
    id: int
    # 移除 create_time 字段，因为 CRUD 返回的数据中没有这个字段
    
    class Config:
        from_attributes = True

# 兼容性字段映射
def std_answer_to_dict(db_obj):
    """将数据库对象转换为字典，保持向后兼容"""
    return {
        'id': db_obj.id,
        'answer': db_obj.answer,
        'answered_by': db_obj.created_by,  # 兼容字段
        'is_valid': db_obj.is_valid,
        'answered_at': db_obj.create_time,  # 兼容字段
        'version': db_obj.version,
        'previous_version_id': db_obj.previous_version_id,
        'std_question_id': db_obj.std_question_id,
        'dataset_id': db_obj.std_question.dataset_id,  # 通过问题获取数据集ID
    }
