from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base

class StdQuestion(Base):
    __tablename__ = "StdQuestion"    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("Dataset.id"), nullable=False, index=True)
    body = Column(Text, nullable=False)  # 统一字段名为body
    question_type = Column(String(50), nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("User.id"), nullable=True, index=True)
    previous_version_id = Column(Integer, ForeignKey("StdQuestion.id"), nullable=True, index=True)      # Relationships
    dataset = relationship("Dataset")
    created_by_user = relationship("User", foreign_keys=[created_by])
    previous_version = relationship("StdQuestion", remote_side=[id])
    std_answers = relationship("StdAnswer", back_populates="std_question", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="QuestionTagRecords", back_populates="std_questions")
    
    # 多对多关系记录
    raw_question_records = relationship("StdQuestionRawQuestionRecord", back_populates="std_question", cascade="all, delete-orphan")
