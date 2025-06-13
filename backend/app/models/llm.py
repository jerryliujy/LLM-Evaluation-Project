from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, DECIMAL, Text, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class LLM(Base):
    __tablename__ = "LLM"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=False, index=True)
    api_endpoint = Column(String(500), nullable=True)
    default_temperature = Column(DECIMAL(3,2), default=0.7)
    max_tokens = Column(Integer, default=4000)    
    top_k = Column(Integer, default=50)
    enable_reasoning = Column(Boolean, nullable=False, server_default=text('0'))
    cost_per_1k_tokens = Column(DECIMAL(8,6), default=0.0006)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=True)
    affiliation = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text('1'), index=True)
    
    # 关系
    evaluation_tasks = relationship("LLMEvaluationTask", foreign_keys="LLMEvaluationTask.model_id", back_populates="model")
    evaluation_tasks_as_evaluator = relationship("LLMEvaluationTask", foreign_keys="LLMEvaluationTask.evaluation_llm_id", back_populates="evaluation_llm")
    answers = relationship("LLMAnswer", back_populates="llm")
    evaluations = relationship("Evaluation", back_populates="evaluator_llm")
