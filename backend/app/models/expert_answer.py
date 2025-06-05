from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class ExpertAnswer(Base):
    __tablename__ = "ExpertAnswer"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("RawQuestion.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    author = Column(Integer, ForeignKey("User.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())   
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    referenced_by_std_answer_id = Column(Integer, ForeignKey("StdAnswer.id"), nullable=True, index=True)

    # 关系
    question = relationship("RawQuestion", back_populates="expert_answers")
    author_user = relationship("User")
    # 被哪个标准回答引用
    referenced_by_std_answer = relationship("StdAnswer", back_populates="referenced_expert_answers")