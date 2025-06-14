"""
LLM Evaluation Task schemas for API serialization
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal
from ..models.llm_evaluation_task import TaskStatus


class SimpleDatasetInfo(BaseModel):
    """简单数据集信息"""
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class SimpleLLMInfo(BaseModel):
    """简单模型信息"""
    id: int
    name: str
    display_name: str
    version: Optional[str] = None
    
    class Config:
        from_attributes = True


class TaskStatusEnum(str, Enum):
    """评测任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluatorTypeEnum(str, Enum):
    """评估者类型枚举"""
    USER = "user"
    LLM = "llm"
    AUTO = "auto"


class PromptTemplateInfo(BaseModel):
    """提示词模板信息（前端展示用）"""
    key: str = Field(..., description="模板标识")
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    template_type: str = Field(..., description="模板类型")
    content: str = Field(..., description="模板内容")
    variables: Dict[str, str] = Field(default_factory=dict, description="模板变量")


class ModelConfigRequest(BaseModel):
    """模型配置请求Schema"""
    model_id: int = Field(..., description="模型ID")
    api_key: str = Field(..., description="API密钥")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    choice_system_prompt: Optional[str] = Field(None, description="选择题系统提示词")
    text_system_prompt: Optional[str] = Field(None, description="问答题系统提示词")
    temperature: Optional[float] = Field(0.7, description="温度参数")  # 改为float类型
    max_tokens: Optional[int] = Field(2000, description="最大token数")
    top_k: Optional[int] = Field(50, description="Top-K采样")
    enable_reasoning: Optional[bool] = Field(False, description="启用推理模式")
    
    class Config:
        # 允许字段验证
        validate_assignment = True


class EvaluationStartRequest(BaseModel):
    """开始评测请求Schema"""
    dataset_id: int = Field(..., description="数据集ID")
    task_name: str = Field(..., description="任务名称")
    model_settings: ModelConfigRequest = Field(..., description="模型配置", alias="model_config")
    evaluation_config: Optional[Dict[str, Any]] = Field(None, description="评测配置")
    is_auto_score: bool = Field(False, description="是否自动评分")
    question_limit: Optional[int] = Field(None, description="限制评测问题数量")
    
    class Config:
        # 允许使用别名
        allow_population_by_field_name = True
        
        
class LLMEvaluationTaskBase(BaseModel):
    """LLM评测任务基础Schema"""
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    dataset_id: int = Field(..., description="数据集ID")
    model_id: int = Field(..., description="LLM模型ID")
    system_prompt: Optional[str] = Field(None, description="系统prompt")
    choice_system_prompt: Optional[str] = Field(None, description="选择题系统prompt")
    text_system_prompt: Optional[str] = Field(None, description="问答题系统prompt")
    choice_evaluation_prompt: Optional[str] = Field(None, description="选择题评估prompt")
    text_evaluation_prompt: Optional[str] = Field(None, description="问答题评估prompt")
    temperature: Optional[Decimal] = Field(Decimal("0.7"), description="温度参数")
    max_tokens: Optional[int] = Field(2000, description="最大token数")
    top_k: Optional[int] = Field(50, description="Top-K采样")
    enable_reasoning: Optional[bool] = Field(False, description="启用推理模式")
    evaluation_prompt: Optional[str] = Field(None, description="评估prompt")


class LLMEvaluationTaskCreate(LLMEvaluationTaskBase):
    """创建LLM评测任务的Schema"""
    api_key: Optional[str] = Field(None, description="API密钥")


class LLMEvaluationTaskUpdate(BaseModel):
    """更新LLM评测任务的Schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    progress: Optional[int] = None
    total_questions: Optional[int] = None
    completed_questions: Optional[int] = None
    failed_questions: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None
    # 新增的prompt字段
    choice_system_prompt: Optional[str] = None
    text_system_prompt: Optional[str] = None
    choice_evaluation_prompt: Optional[str] = None
    text_evaluation_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    evaluation_prompt: Optional[str] = None


class LLMEvaluationTaskResponse(LLMEvaluationTaskBase):
    """LLM评测任务响应Schema"""
    id: int
    created_by: int
    created_at: datetime
    status: TaskStatus
    progress: int
    score: Optional[Decimal] = None
    total_questions: int
    completed_questions: int
    failed_questions: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None    
    # 关联信息
    dataset: Optional[SimpleDatasetInfo] = None
    model: Optional[SimpleLLMInfo] = None
    
    # 运行时信息
    estimated_remaining_time: Optional[int] = Field(None, description="预计剩余时间（秒）")
    questions_per_minute: Optional[float] = Field(None, description="每分钟处理问题数")

    class Config:
        from_attributes = True


class LLMEvaluationTaskProgress(BaseModel):
    """LLM评测任务进度Schema"""
    task_id: int
    status: TaskStatus
    progress: int
    total_questions: int
    completed_questions: int
    failed_questions: int
    estimated_remaining_time: Optional[int] = None
    questions_per_minute: Optional[float] = None
    latest_score: Optional[float] = Field(None, description="最新的评分")
    latest_content: Optional[str] = Field(None, description="最新内容（答案或评测结果）")
    latest_content_type: Optional[str] = Field(None, description="最新内容类型：answer或evaluation")


class LLMAnswerResponse(BaseModel):
    """LLM回答响应Schema"""
    id: int
    llm_id: Optional[int] = None
    task_id: Optional[int] = None
    std_question_id: Optional[int] = None
    prompt_used: Optional[str] = None
    answer: Optional[str] = None
    answered_at: datetime
    is_valid: bool

    class Config:
        from_attributes = True


class EvaluationRequest(BaseModel):
    """评估请求Schema"""
    std_question_id: int
    llm_answer_id: int
    score: Optional[Decimal] = None
    evaluator_type: EvaluatorTypeEnum
    evaluator_id: Optional[int] = None
    notes: Optional[str] = None
    reasoning: Optional[str] = None
    evaluation_prompt: Optional[str] = None


class EvaluationResponse(BaseModel):
    """评估响应Schema"""
    id: int
    std_question_id: int
    llm_answer_id: int
    score: Optional[Decimal] = None
    evaluator_type: EvaluatorTypeEnum
    evaluator_id: Optional[int] = None
    evaluation_time: datetime
    notes: Optional[str] = None
    reasoning: Optional[str] = None
    evaluation_prompt: Optional[str] = None
    is_valid: bool

    class Config:
        from_attributes = True


class AvailableModel(BaseModel):
    """可用模型Schema"""
    id: int = Field(..., description="模型ID")
    name: str = Field(..., description="模型名称")
    display_name: str = Field(..., description="显示名称")
    provider: str = Field(..., description="提供商")
    description: Optional[str] = Field(None, description="模型描述")
    api_endpoint: Optional[str] = Field(None, description="API端点")
    max_tokens: Optional[int] = Field(None, description="最大token限制")
    default_temperature: Optional[Decimal] = Field(None, description="默认温度参数")
    top_k: Optional[int] = Field(None, description="Top-K参数")
    enable_reasoning: bool = Field(False, description="是否启用推理")
    pricing: Optional[Dict[str, float]] = Field(None, description="定价信息")


class TaskResultsRequest(BaseModel):
    """任务结果请求Schema"""
    task_id: int
    include_api_details: bool = Field(False, description="是否包含API详情")
    include_evaluations: bool = Field(True, description="是否包含评估结果")


class TaskStatistics(BaseModel):
    """任务统计Schema"""
    total_questions: int
    completed_questions: int
    failed_questions: int
    success_rate: float
    average_score: Optional[float] = None
    total_cost: Optional[Decimal] = None
    total_tokens: Optional[int] = None
    average_response_time: Optional[float] = None


class EvaluationResultSummary(BaseModel):
    """评测结果摘要Schema"""
    task_id: int
    task_name: str
    dataset_name: str
    model_name: str
    total_questions: int
    successful_count: int
    failed_count: int
    average_score: Optional[float] = None
    completion_rate: float
    total_cost_tokens: Optional[int] = None
    average_response_time: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class EvaluationDownloadRequest(BaseModel):
    """评测结果下载请求Schema"""
    task_id: int = Field(..., description="任务ID")
    format: str = Field("json", description="下载格式")
    include_raw_responses: bool = Field(False, description="是否包含原始响应")
    include_prompts: bool = Field(False, description="是否包含使用的prompt")


class ManualEvaluationEntry(BaseModel):
    """手动录入的单个评测条目"""
    question_id: int = Field(..., description="问题ID")
    answer: str = Field(..., description="LLM回答内容")
    score: float = Field(..., ge=0, le=100, description="得分(0-100)")
    reasoning: Optional[str] = Field(None, description="评分理由")


class ManualEvaluationTaskCreate(BaseModel):
    """手动创建评测任务Schema"""
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    dataset_id: int = Field(..., description="数据集ID")
    model_id: int = Field(..., description="LLM模型ID")
    entries: List[ManualEvaluationEntry] = Field(..., description="评测条目列表")
    
    # 高级配置选项
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    choice_system_prompt: Optional[str] = Field(None, description="选择题系统提示词")
    text_system_prompt: Optional[str] = Field(None, description="问答题系统提示词")
    choice_evaluation_prompt: Optional[str] = Field(None, description="选择题评估提示词")
    text_evaluation_prompt: Optional[str] = Field(None, description="问答题评估提示词")
    evaluation_prompt: Optional[str] = Field(None, description="通用评估提示词")
    temperature: Optional[float] = Field(0.7, description="温度参数")
    max_tokens: Optional[int] = Field(2000, description="最大token数")
    top_k: Optional[int] = Field(50, description="Top-K采样")
    enable_reasoning: Optional[bool] = Field(False, description="启用推理模式")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "手动录入测试任务",
                "description": "手动录入的评测结果",
                "dataset_id": 1,
                "model_id": 1,
                "entries": [
                    {
                        "question_id": 1,
                        "answer": "这是LLM的回答",
                        "score": 85.0,
                        "reasoning": "回答准确性较高",
                    }
                ],
                "system_prompt": "你是一个专业的评测助手",
                "temperature": 0.7,
                "max_tokens": 2000,
                "enable_reasoning": False
            }
        }


class ManualEvaluationTaskResponse(BaseModel):
    """手动评测任务响应Schema"""
    id: int
    name: str
    description: Optional[str]
    dataset: SimpleDatasetInfo
    model: SimpleLLMInfo
    status: TaskStatus
    score: Optional[float]
    total_questions: int
    completed_questions: int
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ManualEvaluationAnswer(BaseModel):
    """手动评测答案信息"""
    id: int
    answer_text: str
    question_id: int
    question_body: str
    question_type: str
    std_answers: List[Dict[str, Any]]
    current_score: Optional[float] = None
    current_reasoning: Optional[str] = None
    model_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ManualEvaluationRequest(BaseModel):
    """手动评测请求"""
    answer_id: int
    score: float = Field(..., ge=0, le=100, description="评分，0-100")
    reasoning: str = Field(..., min_length=1, description="评分理由")


class ManualEvaluationBatchRequest(BaseModel):
    """批量手动评测请求"""
    evaluations: List[ManualEvaluationRequest]


class ManualEvaluationProgress(BaseModel):
    """手动评测进度"""
    total_answers: int
    evaluated_answers: int
    progress_percentage: float
    
    class Config:
        from_attributes = True
