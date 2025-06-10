from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class StdAnswerScoringPointBase(BaseModel):
    answer: str
    point_order: Optional[int] = 0

class StdAnswerScoringPointCreate(StdAnswerScoringPointBase):
    pass

class StdAnswerScoringPoint(StdAnswerScoringPointBase):
    id: int
    std_answer_id: int
    is_valid: bool
    previous_version_id: Optional[int] = None

    class Config:
        from_attributes = True

class StdAnswerBase(BaseModel):
    answer: str
    answered_by: Optional[int] = None  # 统一为answered_by，并改为int类型用户ID

class StdAnswerCreate(StdAnswerBase):
    std_question_id: Optional[int] = None  # 在嵌套创建时不需要，在独立创建时需要
    version: Optional[int] = None
    previous_version_id: Optional[int] = None
    scoring_points: List[StdAnswerScoringPointCreate] = []
    referenced_raw_answer_ids: List[int] = []
    referenced_expert_answer_ids: List[int] = []

class StdAnswerUpdate(BaseModel):
    answer: Optional[str] = None
    answered_by: Optional[int] = None  # 统一为answered_by
    previous_version_id: Optional[int] = None
    scoring_points: Optional[List[StdAnswerScoringPointCreate]] = None
    referenced_raw_answer_ids: Optional[List[int]] = None
    referenced_expert_answer_ids: Optional[List[int]] = None

class StdAnswer(StdAnswerBase):
    id: int
    std_question_id: int
    is_valid: bool
    answered_at: datetime  # 统一为answered_at
    previous_version_id: Optional[int] = None

    class Config:
        from_attributes = True

class StdAnswerWithScoringPoints(StdAnswer):
    scoring_points: List[StdAnswerScoringPoint] = []

    class Config:
        from_attributes = True


# 添加缺失的响应类
class StdAnswerScoringPointResponse(StdAnswerScoringPoint):
    """标准答案评分点响应模型"""
    class Config:
        from_attributes = True

class StdAnswerResponse(StdAnswerWithScoringPoints):
    """标准答案响应模型"""
    std_question: Optional[dict] = None  # 添加关联的标准问题信息
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_db_model(cls, db_obj):
        """从数据库对象创建响应模型"""
        # 转换基本字段
        data = {
            'id': db_obj.id,
            'answer': db_obj.answer,
            'answered_by': db_obj.answered_by,
            'std_question_id': db_obj.std_question_id,
            'is_valid': db_obj.is_valid,
            'answered_at': db_obj.answered_at,
            'previous_version_id': db_obj.previous_version_id,
        }
        
        # 转换评分点
        if hasattr(db_obj, 'scoring_points') and db_obj.scoring_points:
            data['scoring_points'] = [
                {
                    'id': sp.id,
                    'answer': sp.answer,
                    'point_order': sp.point_order,
                    'std_answer_id': sp.std_answer_id,
                    'is_valid': sp.is_valid,
                    'previous_version_id': sp.previous_version_id
                }
                for sp in db_obj.scoring_points
            ]
        else:
            data['scoring_points'] = []
        
        # 转换关联的标准问题
        if hasattr(db_obj, 'std_question') and db_obj.std_question:
            data['std_question'] = {
                'id': db_obj.std_question.id,
                'body': db_obj.std_question.body,
                'question_type': db_obj.std_question.question_type,
                'dataset_id': db_obj.std_question.dataset_id,
                'is_valid': db_obj.std_question.is_valid,
                'created_at': db_obj.std_question.created_at,
                'previous_version_id': db_obj.std_question.previous_version_id
            }
        else:
            data['std_question'] = None
        
        return cls(**data)
