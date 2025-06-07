from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class ExpertAnswer(Base):
    __tablename__ = "ExpertAnswer"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("RawQuestion.id"), nullable=False, index=True)
    answer = Column(Text, nullable=False)
    answered_by = Column(Integer, ForeignKey("User.id"), nullable=False, index=True)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())   
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    question = relationship("RawQuestion", back_populates="expert_answers")
    author_user = relationship("User")
    
    # 多对多关系记录
    std_answer_records = relationship("StdAnswerExpertAnswerRecord", back_populates="expert_answer", cascade="all, delete-orphan")