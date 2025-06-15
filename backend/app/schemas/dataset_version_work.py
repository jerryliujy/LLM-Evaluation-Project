"""
Dataset Version Work schemas for API serialization
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class WorkStatus(str, Enum):
    """版本工作状态枚举"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class QuestionType(str, Enum):
    """问题类型枚举"""
    CHOICE = "choice"
    TEXT = "text"


# ============ Version Tag Schemas ============

class VersionTagBase(BaseModel):
    """版本标签基础Schema"""
    tag_label: str = Field(..., description="标签名称")
    is_deleted: bool = Field(False, description="是否删除")
    is_new: bool = Field(False, description="是否新增")


class VersionTagCreate(VersionTagBase):
    """创建版本标签Schema"""
    version_question_id: int = Field(..., description="版本问题ID")


class VersionTagResponse(VersionTagBase):
    """版本标签响应Schema"""
    id: int
    version_work_id: int
    version_question_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Version Question Schemas ============

class VersionStdQuestionBase(BaseModel):
    """版本标准问题基础Schema"""
    is_modified: bool = Field(False, description="是否修改")
    is_new: bool = Field(False, description="是否新增")
    is_deleted: bool = Field(False, description="是否删除")
    modified_body: Optional[str] = Field(None, description="修改后的问题内容")
    modified_question_type: Optional[QuestionType] = Field(None, description="修改后的问题类型")


class VersionStdQuestionCreate(VersionStdQuestionBase):
    """创建版本标准问题Schema"""
    original_question_id: Optional[int] = Field(None, description="原始问题ID")


class VersionStdQuestionUpdate(BaseModel):
    """更新版本标准问题Schema"""
    is_modified: Optional[bool] = None
    is_new: Optional[bool] = None
    is_deleted: Optional[bool] = None
    modified_body: Optional[str] = None
    modified_question_type: Optional[QuestionType] = None


class VersionStdQuestionResponse(VersionStdQuestionBase):
    """版本标准问题响应Schema"""
    id: int
    version_work_id: int
    original_question_id: Optional[int]
    created_at: datetime
    version_tags: List[VersionTagResponse] = []
    
    class Config:
        from_attributes = True


# ============ Version Answer Schemas ============

class VersionStdAnswerBase(BaseModel):
    """版本标准答案基础Schema"""
    is_modified: bool = Field(False, description="是否修改")
    is_deleted: bool = Field(False, description="是否删除")
    is_new: bool = Field(True, description="是否新增")
    modified_answer: Optional[str] = Field(None, description="修改后的答案内容")
    modified_answered_by: Optional[int] = Field(None, description="修改后的回答者ID")


class VersionStdAnswerCreate(VersionStdAnswerBase):
    """创建版本标准答案Schema"""
    original_answer_id: Optional[int] = Field(None, description="原始答案ID")


class VersionStdAnswerWithScoringPointsCreate(VersionStdAnswerCreate):
    """创建包含得分点的版本标准答案Schema"""
    scoring_points_data: Optional[List[Dict[str, Any]]] = Field(None, description="得分点数据列表")


class VersionStdAnswerUpdate(BaseModel):
    """更新版本标准答案Schema"""
    is_modified: Optional[bool] = None
    is_deleted: Optional[bool] = None
    is_new: Optional[bool] = None
    modified_answer: Optional[str] = None
    modified_answered_by: Optional[int] = None


class VersionStdAnswerResponse(VersionStdAnswerBase):
    """版本标准答案响应Schema"""
    id: int
    version_work_id: int
    original_answer_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Version Scoring Point Schemas ============

class VersionScoringPointBase(BaseModel):
    """版本得分点基础Schema"""
    is_modified: bool = Field(False, description="是否修改")
    is_deleted: bool = Field(False, description="是否删除")
    is_new: bool = Field(True, description="是否新增")
    modified_answer: Optional[str] = Field(None, description="修改后的得分点内容")
    modified_point_order: Optional[int] = Field(None, description="修改后的排序")


class VersionScoringPointCreate(VersionScoringPointBase):
    """创建版本得分点Schema"""
    version_answer_id: int = Field(..., description="版本答案ID")
    original_point_id: Optional[int] = Field(None, description="原始得分点ID")


class VersionScoringPointUpdate(BaseModel):
    """更新版本得分点Schema"""
    is_modified: Optional[bool] = None
    is_deleted: Optional[bool] = None
    is_new: Optional[bool] = None
    modified_answer: Optional[str] = None
    modified_point_order: Optional[int] = None


class VersionScoringPointResponse(VersionScoringPointBase):
    """版本得分点响应Schema"""
    id: int
    version_work_id: int
    version_answer_id: int
    original_point_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Dataset Version Work Schemas ============

class DatasetVersionWorkBase(BaseModel):
    """数据集版本工作基础Schema"""
    dataset_id: int = Field(..., description="数据集ID")
    current_version: int = Field(..., description="当前版本号")
    target_version: int = Field(..., description="目标版本号")
    work_description: Optional[str] = Field(None, description="工作描述")
    notes: Optional[str] = Field(None, description="备注")


class DatasetVersionWorkCreate(DatasetVersionWorkBase):
    """创建数据集版本工作Schema"""
    pass


class DatasetVersionWorkUpdate(BaseModel):
    """更新数据集版本工作Schema"""
    work_status: Optional[WorkStatus] = None
    work_description: Optional[str] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None


class DatasetVersionWorkResponse(DatasetVersionWorkBase):
    """数据集版本工作响应Schema"""
    id: int
    work_status: WorkStatus
    created_by: int
    created_at: datetime
    completed_at: Optional[datetime]
    version_questions: List[VersionStdQuestionResponse] = []
    
    class Config:
        from_attributes = True


# ============ Summary Schemas ============

class DatasetVersionWorkSummary(BaseModel):
    """数据集版本工作概要Schema"""
    id: int
    dataset_id: int
    dataset_name: str
    current_version: int
    target_version: int
    work_status: WorkStatus
    work_description: Optional[str]
    created_by: int
    created_at: datetime
    completed_at: Optional[datetime]
    
    # 统计信息
    total_questions: int = 0
    modified_questions: int = 0
    new_questions: int = 0
    deleted_questions: int = 0
    
    class Config:
        from_attributes = True


# ============ Complete Standard QA Creation Schema ============

class VersionStdQaPairCreate(BaseModel):
    """创建完整版本标准问答对Schema"""
    question: str = Field(..., description="问题内容")
    answer: str = Field(..., description="答案内容")
    question_type: QuestionType = Field(QuestionType.TEXT, description="问题类型")
    key_points: List[Dict[str, Any]] = Field(default_factory=list, description="得分点列表")
    raw_question_ids: List[int] = Field(default_factory=list, description="关联的原始问题ID列表")
    raw_answer_ids: List[int] = Field(default_factory=list, description="关联的原始答案ID列表")
    expert_answer_ids: List[int] = Field(default_factory=list, description="关联的专家答案ID列表")
    tags: List[str] = Field(default_factory=list, description="标签列表")


class VersionStdQaPairResponse(BaseModel):
    """版本标准问答对响应Schema"""
    question_id: int
    answer_id: int
    scoring_point_ids: List[int] = Field(default_factory=list)
    tag_ids: List[int] = Field(default_factory=list)
    
    class Config:
        from_attributes = True
