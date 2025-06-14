"""
LLM Evaluation Task models for managing background evaluation processes
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, DECIMAL, JSON, Enum as SQLEnum, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..db.database import Base


class TaskStatus(enum.Enum):
    """评测任务状态 - 5个阶段"""
    CONFIG_PARAMS = "config_params"            # 阶段1：参数配置
    CONFIG_PROMPTS = "config_prompts"          # 阶段2：提示词配置
    GENERATING_ANSWERS = "generating_answers"  # 阶段3：生成答案中
    EVALUATING_ANSWERS = "evaluating_answers"  # 阶段4：评测答案中
    COMPLETED = "completed"                    # 阶段5：全部完成，可查看结果
    FAILED = "failed"                          # 失败
    CANCELLED = "cancelled"                    # 已取消


class LLMEvaluationTask(Base):
    """LLM评测任务表"""
    __tablename__ = "LLMEvaluationTask"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # 任务名称
    description = Column(Text, nullable=True)  # 任务描述
    dataset_id = Column(Integer, ForeignKey("Dataset.id"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("User.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), index=True)
    
    # 任务状态
    status = Column(SQLEnum(TaskStatus, values_callable=lambda x: [e.value for e in x]), 
                   default=TaskStatus.CONFIG_PARAMS, nullable=False, index=True)
    progress = Column(Integer, server_default=text('0'), nullable=False)  # 进度百分比
    score = Column(DECIMAL(5, 2), nullable=True)  # 任务评分
    total_questions = Column(Integer, server_default=text('0'), nullable=False)
    completed_questions = Column(Integer, server_default=text('0'), nullable=False)
    failed_questions = Column(Integer, server_default=text('0'), nullable=False)
    
    # 模型配置
    model_id = Column(Integer, ForeignKey("LLM.id"), nullable=False, index=True)  # LLM模型ID    
    api_key_hash = Column(String(255), nullable=True)  # API密钥（加密存储）
      # Prompt配置
    system_prompt = Column(Text, nullable=True)  # 系统prompt
    choice_system_prompt = Column(Text, nullable=True)  # 选择题系统prompt
    text_system_prompt = Column(Text, nullable=True)  # 问答题系统prompt
    choice_evaluation_prompt = Column(Text, nullable=True)  # 选择题评估prompt
    text_evaluation_prompt = Column(Text, nullable=True)  # 问答题评估prompt
    temperature = Column(DECIMAL(3, 2), server_default=text('0.7'))  # 温度参数    
    max_tokens = Column(Integer, server_default=text('2000'))  # 最大token数
    top_k = Column(Integer, server_default=text('50'))  # Top-K采样
    enable_reasoning = Column(Boolean, server_default=text('0'), nullable=False)  # 启用推理模式
    
    # 自动评估配置
    evaluation_prompt = Column(Text, nullable=True)  # 评估prompt（兼容性保留）
    
    # 时间记录
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 错误和结果
    error_message = Column(Text, nullable=True)    # 关系
    dataset = relationship("Dataset")
    user = relationship("User")  # 创建者
    model = relationship("LLM", foreign_keys=[model_id], back_populates="evaluation_tasks")  # 评测模型
    llm_answers = relationship("LLMAnswer", back_populates="task")
    
    def __repr__(self):
        return f"<LLMEvaluationTask(id={self.id}, name={self.name}, status={self.status})>"
