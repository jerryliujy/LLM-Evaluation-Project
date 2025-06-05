from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class StdAnswerRawAnswerRecord(Base):
    __tablename__ = "StdAnswerRawAnswerRecord"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    std_answer_id = Column(Integer, ForeignKey("StdAnswer.id"), nullable=False)
    raw_answer_id = Column(Integer, ForeignKey("RawAnswer.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    created_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # 关系
    std_answer = relationship("StdAnswer", back_populates="raw_answer_records")
    raw_answer = relationship("RawAnswer", back_populates="std_answer_records")


class StdAnswerExpertAnswerRecord(Base):
    __tablename__ = "StdAnswerExpertAnswerRecord"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    std_answer_id = Column(Integer, ForeignKey("StdAnswer.id"), nullable=False)
    expert_answer_id = Column(Integer, ForeignKey("ExpertAnswer.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    created_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # 关系
    std_answer = relationship("StdAnswer", back_populates="expert_answer_records")
    expert_answer = relationship("ExpertAnswer", back_populates="std_answer_records")


class StdQuestionRawQuestionRecord(Base):
    __tablename__ = "StdQuestionRawQuestionRecord"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    std_question_id = Column(Integer, ForeignKey("StdQuestion.id"), nullable=False)
    raw_question_id = Column(Integer, ForeignKey("RawQuestion.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    created_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # 关系
    std_question = relationship("StdQuestion", back_populates="raw_question_records")
    raw_question = relationship("RawQuestion", back_populates="std_question_records")
