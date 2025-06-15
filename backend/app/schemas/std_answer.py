from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class StdAnswerBase(BaseModel):
    std_question_id: int
    answer: str
    is_valid: bool = True
    answered_by: Optional[int] = None  # 创建时传入用户ID
    version: int = 1
    previous_version_id: Optional[int] = None    # 版本区间字段
    original_version_id: Optional[int] = None  # 最早出现的版本
    current_version_id: Optional[int] = None   # 当前有效的最新版本

class StdAnswerCreate(StdAnswerBase):
    pass

class StdAnswerUpdate(BaseModel):
    std_question_id: Optional[int] = None
    answer: Optional[str] = None
    is_valid: Optional[bool] = None
    # 明确排除用户相关和版本管理字段，这些在普通编辑时不应被修改
    # answered_by, version, previous_version_id 等字段不包含在这里
    scoring_points: Optional[List['StdAnswerScoringPointUpdate']] = None  # 添加评分点更新支持
    referenced_raw_answer_ids: Optional[List[int]] = None  # 引用的原始回答ID列表
    referenced_expert_answer_ids: Optional[List[int]] = None  # 引用的专家回答ID列表

class StdAnswerResponse(StdAnswerBase):
    id: int
    answered_at: datetime  # 使用 answered_at 而不是 create_time
    answered_by: Optional[str] = None  # 响应时返回用户名而不是ID
    scoring_points: Optional[List['StdAnswerScoringPointResponse']] = None  # 添加得分点列表
    std_question: Optional[dict] = None  # 添加关联的标准问题信息
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_db_model(cls, db_obj):
        """从数据库对象创建响应对象，确保正确的数据转换"""
        return cls(
            id=db_obj.id,
            std_question_id=db_obj.std_question_id,
            answer=db_obj.answer,
            is_valid=db_obj.is_valid,
            answered_by=db_obj.answered_by_user.username if db_obj.answered_by_user else "unknown",
            answered_at=db_obj.answered_at,
            version=db_obj.version,
            previous_version_id=db_obj.previous_version_id,
            original_version_id=db_obj.original_version_id,
            current_version_id=db_obj.current_version_id,            scoring_points=[
                StdAnswerScoringPointResponse.from_db_model(sp) 
                for sp in db_obj.scoring_points if sp.is_valid
            ] if db_obj.scoring_points else [],
            std_question={
                "id": db_obj.std_question.id,
                "body": db_obj.std_question.body,
                "question_type": db_obj.std_question.question_type,
                "dataset_id": db_obj.std_question.dataset_id
            } if db_obj.std_question else None
        )

class StdAnswerInDB(StdAnswerBase):
    id: int
    answered_at: datetime  
    answered_by: Optional[str] = None  
    
    class Config:
        from_attributes = True

class StdAnswerScoringPointBase(BaseModel):
    std_answer_id: int
    answer: str  # 使用 answer 字段匹配模型的 @property
    point_order: int = 0
    is_valid: bool = True
    answered_by: Optional[int] = None  # 创建时传入用户ID
    previous_version_id: Optional[int] = None

class StdAnswerScoringPointCreate(StdAnswerScoringPointBase):
    pass

class StdAnswerScoringPointUpdate(BaseModel):
    answer: Optional[str] = None  # 使用 answer 字段匹配模型的 @property
    point_order: Optional[int] = None
    is_valid: Optional[bool] = None
    # 明确排除用户相关和版本管理字段
    # answered_by, previous_version_id 等字段不包含在这里

class StdAnswerScoringPointResponse(StdAnswerScoringPointBase):
    id: int
    version: int = 1
    answered_by: Optional[str] = None  # 响应时返回用户名
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_db_model(cls, db_obj):
        """从数据库对象创建响应对象，确保正确的数据转换"""
        return cls(
            id=db_obj.id,
            std_answer_id=db_obj.std_answer_id,
            answer=db_obj.answer,
            point_order=db_obj.point_order,
            is_valid=db_obj.is_valid,
            answered_by=db_obj.answered_by_user.username if db_obj.answered_by_user else "unknown",
            version=db_obj.version,
            previous_version_id=db_obj.previous_version_id
        )

class StdAnswerScoringPointInDB(StdAnswerScoringPointBase):
    id: int
    
    class Config:
        from_attributes = True

# 更新前向引用
StdAnswerUpdate.model_rebuild()
StdAnswerResponse.model_rebuild()
