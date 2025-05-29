from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base 

class RawQuestion(Base):
    __tablename__ = "RawQuestion"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), index=True, nullable=False) 
    url = Column(String(1024), unique=True, nullable=True)
    body = Column(Text, nullable=True)
    vote_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    author = Column(String(255), nullable=True)
    tags = Column(JSON, nullable=True)
    issued_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 记录入库时间
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    raw_answers = relationship("RawAnswer", back_populates="question", cascade="all, delete-orphan", lazy="selectin")
    expert_answers = relationship("ExpertAnswer", back_populates="question", cascade="all, delete-orphan", lazy="selectin")