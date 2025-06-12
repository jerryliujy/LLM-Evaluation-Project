"""
LLM Answer schemas for API serialization
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.schemas.llm import LLM


class LLMSimple(BaseModel):
    """简化的LLM schema，用于列表显示"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    display_name: str
    provider: str
    description: Optional[str] = None
    is_active: bool


class LLMAnswerScoringPointBase(BaseModel):
    """LLM回答评分点基础schema"""
    answer: str
    point_order: Optional[int] = 0


class LLMAnswerScoringPointCreate(LLMAnswerScoringPointBase):
    """创建LLM回答评分点的schema"""
    pass


class LLMAnswerScoringPoint(LLMAnswerScoringPointBase):
    """LLM回答评分点响应schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    llm_answer_id: int


class LLMAnswerBase(BaseModel):
    """LLM回答基础schema"""
    llm_id: int
    std_question_id: int
    answer: str
    api_request_id: Optional[str] = None
    model_params: Optional[str] = None
    cost_tokens: Optional[int] = None


class LLMAnswerCreate(LLMAnswerBase):
    """创建LLM回答的schema"""
    scoring_points: List[LLMAnswerScoringPointCreate] = []


class LLMAnswerUpdate(BaseModel):
    """更新LLM回答的schema"""
    answer: Optional[str] = None
    is_valid: Optional[bool] = None
    scoring_points: Optional[List[LLMAnswerScoringPointCreate]] = None


class LLMAnswer(LLMAnswerBase):
    """LLM回答响应schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    answered_at: datetime
    is_valid: bool


class LLMAnswerWithDetails(LLMAnswer):
    """包含详细信息的LLM回答schema"""
    scoring_points: List[LLMAnswerScoringPoint] = []
    llm: Optional["LLM"] = None


class LLMEvaluationRequest(BaseModel):
    """LLM评估请求schema"""
    llm_answers: List[LLMAnswerCreate]
    evaluation_config: Optional[dict] = None


class LLMEvaluationResponse(BaseModel):
    """LLM评估结果响应schema"""
    model_config = ConfigDict(from_attributes=True)
    
    evaluation_id: str
    status: str  # "processing", "completed", "failed"
    created_answers: List[LLMAnswer] = []
    evaluation_results: Optional[dict] = None


class MarketplaceDatasetInfo(BaseModel):
    """数据集市场信息schema"""
    id: int
    name: str
    description: str
    version: int
    question_count: int
    choice_question_count: int = 0
    text_question_count: int = 0
    is_public: bool
    created_by: int
    create_time: datetime


class DatasetDownloadResponse(BaseModel):
    """数据集下载响应schema"""
    dataset_info: MarketplaceDatasetInfo
    questions: List[dict]
    download_url: Optional[str] = None
