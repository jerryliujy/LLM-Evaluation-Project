from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class RawAnswer(Base):
    __tablename__ = "RawAnswer"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("RawQuestion.id"), nullable=False, index=True)
    answer = Column(Text, nullable=False)  # 改为answer匹配测试数据
    upvotes = Column(String(20), default=0)   # 改为upvotes匹配测试数据
    answered_by = Column(String(255), nullable=True)  # 改为answered_by匹配测试数据
    answered_at = Column(DateTime, nullable=True) 
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    referenced_by_std_answer_id = Column(Integer, ForeignKey("StdAnswer.id"), nullable=True, index=True)

    # 关系
    question = relationship("RawQuestion", back_populates="raw_answers")
    # 被哪个标准回答引用
    referenced_by_std_answer = relationship("StdAnswer", back_populates="referenced_raw_answers")