"""
LLM Answer models for storing LLM responses and evaluations
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base


class LLMAnswer(Base):
    """LLM回答表"""
    __tablename__ = "LLMAnswer"

    id = Column(Integer, primary_key=True, index=True)
    llm_id = Column(Integer, ForeignKey("LLM.id"), nullable=True, index=True)
    task_id = Column(Integer, ForeignKey("LLMEvaluationTask.id"), nullable=True, index=True)
    std_question_id = Column(Integer, ForeignKey("StdQuestion.id"), nullable=True, index=True)
    prompt_used = Column(Text, nullable=True)  # 使用的提示词
    answer = Column(Text, nullable=True)  # LLM的回答内容
    answered_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    is_valid = Column(Boolean, default=True, nullable=False, index=True)
    
    # 关系
    llm = relationship("LLM", back_populates="answers")
    std_question = relationship("StdQuestion")
    task = relationship("LLMEvaluationTask", back_populates="llm_answers")
    evaluations = relationship("Evaluation", back_populates="llm_answer", cascade="all, delete-orphan")
