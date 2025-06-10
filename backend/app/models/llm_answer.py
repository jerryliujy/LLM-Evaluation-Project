"""
LLM Answer models for storing LLM responses and evaluations
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base


class LLM(Base):
    """LLM模型表"""
    __tablename__ = "LLM"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # LLM名称，如"qwen-plus"
    version = Column(String(50), nullable=False)  # 版本
    affiliation = Column(String(50), nullable=True)  # 所属机构
    
    # 关系
    answers = relationship("LLMAnswer", back_populates="llm", cascade="all, delete-orphan")


class LLMAnswer(Base):
    """LLM回答表"""
    __tablename__ = "LLMAnswer"

    id = Column(Integer, primary_key=True, index=True)
    llm_id = Column(Integer, ForeignKey("LLM.id"), nullable=False, index=True)
    std_question_id = Column(Integer, ForeignKey("StdQuestion.id"), nullable=False, index=True)
    answer = Column(Text, nullable=False)  # LLM的回答内容
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    is_valid = Column(Boolean, default=True, nullable=False, index=True)
    
    # API调用相关信息（可选）
    api_request_id = Column(String(255), nullable=True)  # API请求ID
    model_params = Column(Text, nullable=True)  # 模型参数JSON
    cost_tokens = Column(Integer, nullable=True)  # 消耗的token数
    
    # 关系
    llm = relationship("LLM", back_populates="answers")
    std_question = relationship("StdQuestion")
    scoring_points = relationship("LLMAnswerScoringPoint", back_populates="llm_answer", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="llm_answer", cascade="all, delete-orphan")


class LLMAnswerScoringPoint(Base):
    """LLM回答评分点"""
    __tablename__ = "LLMAnswerScoringPoint"

    id = Column(Integer, primary_key=True, index=True)
    llm_answer_id = Column(Integer, ForeignKey("LLMAnswer.id"), nullable=False, index=True)
    answer = Column(Text, nullable=False)  # 评分点内容
    point_order = Column(Integer, default=0)  # 评分点顺序

    # 关系
    llm_answer = relationship("LLMAnswer", back_populates="scoring_points")
