"""
Evaluation model for storing LLM and user evaluations
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum, DECIMAL, text
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
    score = Column(DECIMAL(5, 2), nullable=True)  # 评分 (0-100)
    evaluator_type = Column(SQLEnum(EvaluatorType, values_callable=lambda x: [e.value for e in x]), 
                            default=EvaluatorType.LLM, nullable=False)   # 评估者类型
    evaluator_id = Column(Integer, nullable=False)  # 用户ID或LLM ID
    evaluation_time = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), index=True)
    notes = Column(Text, nullable=True)      # 评估备注
    reasoning = Column(Text, nullable=True)  # 评估理由（特别用于自动评估）
    evaluation_prompt = Column(Text, nullable=True)  # 使用的评估提示词
    is_valid = Column(Boolean, server_default=text('1'), nullable=False)
    
    # 关系
    std_question = relationship("StdQuestion")
    llm_answer = relationship("LLMAnswer", back_populates="evaluations")
    
    def __repr__(self):
        return f"<Evaluation(id={self.id}, llm_answer_id={self.llm_answer_id}, evaluator_type={self.evaluator_type}, score={self.score})>"