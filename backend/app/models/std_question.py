from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base

class StdQuestion(Base):
    __tablename__ = "StdQuestion"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("Dataset.id"), nullable=False, index=True)
    raw_question_id = Column(Integer, ForeignKey("RawQuestion.id"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    create_time = Column(DateTime(timezone=True), server_default=func.now())
    question_type = Column(String(50), nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False, index=True)
    created_by = Column(String(100), nullable=True)
    version = Column(Integer, default=1, nullable=False, index=True)
    previous_version_id = Column(Integer, ForeignKey("StdQuestion.id"), nullable=True)    # Relationships
    dataset = relationship("Dataset")
    raw_question = relationship("RawQuestion")
    previous_version = relationship("StdQuestion", remote_side=[id])
    std_answers = relationship("StdAnswer", back_populates="std_question", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="QuestionTagRecords", back_populates="std_questions")
