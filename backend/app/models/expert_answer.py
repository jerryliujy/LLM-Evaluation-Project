from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class ExpertAnswer(Base):
    __tablename__ = "ExpertAnswer"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("RawQuestion.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=False, index=True)
    vote_count = Column(Integer, default=0, nullable=True)
    author = Column(Integer, ForeignKey("User.id"), nullable=False, index=True)  # 改为引用User表
    created_at = Column(DateTime(timezone=True), server_default=func.now())   
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    question = relationship("RawQuestion", back_populates="expert_answers")
    author_user = relationship("User")  # 添加与User的关系