from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


# 基础关系记录模型
class StdAnswerRawAnswerRecordBase(BaseModel):
    std_answer_id: int
    raw_answer_id: int
    notes: Optional[str] = None
    created_by: Optional[str] = None


class StdAnswerRawAnswerRecordCreate(StdAnswerRawAnswerRecordBase):
    pass


class StdAnswerRawAnswerRecord(StdAnswerRawAnswerRecordBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime


class StdAnswerExpertAnswerRecordBase(BaseModel):
    std_answer_id: int
    expert_answer_id: int
    notes: Optional[str] = None
    created_by: Optional[str] = None


class StdAnswerExpertAnswerRecordCreate(StdAnswerExpertAnswerRecordBase):
    pass


class StdAnswerExpertAnswerRecord(StdAnswerExpertAnswerRecordBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime


class StdQuestionRawQuestionRecordBase(BaseModel):
    std_question_id: int
    raw_question_id: int
    notes: Optional[str] = None
    created_by: Optional[str] = None

class StdQuestionRawQuestionRecordCreate(StdQuestionRawQuestionRecordBase):
    pass

class StdQuestionRawQuestionRecord(StdQuestionRawQuestionRecordBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime


# 批量创建请求模型
class CreateStandardQAWithReferencesRequest(BaseModel):
    """批量创建标准问答的请求模型"""
    
    # 标准问题字段
    dataset_id: int
    question_text: str
    difficulty_level: Optional[str] = None
    knowledge_points: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None
    
    # 标准答案字段
    answer_text: str
    answer_type: Optional[str] = None
    scoring_points: Optional[List[dict]] = None
    total_score: Optional[float] = None
    explanation: Optional[str] = None
    
    # 关系记录
    raw_question_relations: Optional[List[dict]] = []
    raw_answer_relations: Optional[List[dict]] = []
    expert_answer_relations: Optional[List[dict]] = []

# 响应模型
class StdQAWithRelationsResponse(BaseModel):
    """带关系的标准问答响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    std_question: dict
    std_answer: dict
    raw_question_relations: List[StdQuestionRawQuestionRecord] = []
    raw_answer_relations: List[StdAnswerRawAnswerRecord] = []
    expert_answer_relations: List[StdAnswerExpertAnswerRecord] = []
