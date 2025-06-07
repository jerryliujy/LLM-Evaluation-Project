"""
Evaluation model for storing LLM and user evaluations
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..db.database import Base


class EvaluatorType(enum.Enum):
    """评估者类型枚举"""
    USER = "user"
    LLM = "llm"


class Evaluation(Base):
    """评估表 - 支持LLM或用户进行多个评估"""
    __tablename__ = "Evaluation"
    
    id = Column(Integer, primary_key=True, index=True)
    std_answer_id = Column(Integer, ForeignKey("std_answers.id"), nullable=False, index=True)
    evaluator_type = Column(Enum(EvaluatorType), nullable=False)  # 评估者类型
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 用户ID，LLM评估时为NULL
    evaluation_time = Column(DateTime(timezone=True), server_default=func.now())   
    score = Column(Integer, nullable=False)  # 评分
    notes = Column(Text, nullable=True)  # 评估备注
    is_valid = Column(Boolean, default=True, nullable=False)
    
    # 关系
    # std_answer = relationship("StdAnswer", back_populates="evaluation")
    # evaluator = relationship("User", foreign_keys=[evaluator_id])
    
    def __repr__(self):
        return f"<Evaluation(id={self.id}, std_answer_id={self.std_answer_id}, evaluator_type={self.evaluator_type}, score={self.score})>"