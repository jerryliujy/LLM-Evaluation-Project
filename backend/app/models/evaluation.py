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
    """评估表 - 对LLM回答进行评估"""
    __tablename__ = "Evaluation"
    
    id = Column(Integer, primary_key=True, index=True)
    std_question_id = Column(Integer, ForeignKey("StdQuestion.id"), nullable=False, index=True)
    llm_answer_id = Column(Integer, ForeignKey("LLMAnswer.id"), nullable=False, index=True)
    score = Column(Integer, nullable=False)  # 评分 (0-100)
    evaluator_type = Column(Enum(EvaluatorType), nullable=False)  # 评估者类型
    evaluator_id = Column(Integer, ForeignKey("User.id"), nullable=True)  # 用户ID，自动评估时为NULL
    evaluation_criteria = Column(Text, nullable=True)  # 评估标准
    feedback = Column(Text, nullable=True)  # 评估反馈  
    evaluation_time = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)  # 评估备注
    is_valid = Column(Boolean, default=True, nullable=False)
    
    # 关系
    std_question = relationship("StdQuestion")
    llm_answer = relationship("LLMAnswer", back_populates="evaluations")
    evaluator = relationship("User", foreign_keys=[evaluator_id])
    
    def __repr__(self):
        return f"<Evaluation(id={self.id}, std_answer_id={self.std_answer_id}, evaluator_type={self.evaluator_type}, score={self.score})>"