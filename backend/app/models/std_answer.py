from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base

class StdAnswer(Base):
    __tablename__ = "StdAnswer"

    id = Column(Integer, primary_key=True, index=True)
    std_question_id = Column(Integer, ForeignKey("StdQuestion.id"), nullable=False, index=True)
    answer = Column(Text, nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False, index=True)
    answered_by = Column(Integer, ForeignKey("User.id"), nullable=True, index=True)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    std_question = relationship("StdQuestion", back_populates="std_answers")
    answered_by_user = relationship("User", foreign_keys=[answered_by])
    previous_version = relationship("StdAnswer", remote_side=[id])
    scoring_points = relationship("StdAnswerScoringPoint", back_populates="std_answer", cascade="all, delete-orphan")
    previous_version_id = Column(Integer, ForeignKey("StdAnswer.id"), nullable=True, index=True)
    
    # 多对多关系记录
    raw_answer_records = relationship("StdAnswerRawAnswerRecord", back_populates="std_answer", cascade="all, delete-orphan")
    expert_answer_records = relationship("StdAnswerExpertAnswerRecord", back_populates="std_answer", cascade="all, delete-orphan")
    
    # 评估关系
    # evaluations = relationship("Evaluation", back_populates="std_answer", cascade="all, delete-orphan")

class StdAnswerScoringPoint(Base):
    __tablename__ = "StdAnswerScoringPoint"

    id = Column(Integer, primary_key=True, index=True)
    std_answer_id = Column(Integer, ForeignKey("StdAnswer.id"), nullable=False, index=True)
    answer = Column(Text, nullable=False)  # 统一字段名为answer
    point_order = Column(Integer, default=0)
    is_valid = Column(Boolean, default=True, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("User.id"), nullable=True, index=True)
    create_time = Column(DateTime(timezone=True), server_default=func.now())
    previous_version_id = Column(Integer, ForeignKey("StdAnswerScoringPoint.id"), nullable=True, index=True)

    # Relationships
    std_answer = relationship("StdAnswer", back_populates="scoring_points")
    created_by_user = relationship("User", foreign_keys=[created_by])
    previous_version = relationship("StdAnswerScoringPoint", remote_side=[id])
