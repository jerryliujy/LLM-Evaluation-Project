from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class RawAnswer(Base):
    __tablename__ = "RawAnswer"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("RawQuestion.id"), nullable=False, index=True)
    answer = Column(Text, nullable=False)  
    upvotes = Column(String(20), default=0)   
    answered_by = Column(String(255), nullable=True) 
    answered_at = Column(DateTime, nullable=True) 
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    question = relationship("RawQuestion", back_populates="raw_answers")
    
    # 多对多关系记录
    std_answer_records = relationship("StdAnswerRawAnswerRecord", back_populates="raw_answer", cascade="all, delete-orphan")