from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class RawQuestion(Base):
    __tablename__ = "RawQuestion"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(191), index=True, nullable=False) 
    url = Column(String(191), unique=True, nullable=True)
    body = Column(Text, nullable=True)
    votes = Column(String(20), nullable=True)  # 改为votes匹配测试数据
    views = Column(String(20), nullable=True)  # 支持"1.1m"格式
    author = Column(String(255), nullable=True)    
    tags_json = Column(JSON, nullable=True)  # 原始JSON格式的tags，用于导入时临时存储
    issued_at = Column(DateTime, nullable=True)    
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))  # 记录入库时间
    created_by = Column(Integer, ForeignKey("User.id"), nullable=True, index=True)  # 创建者用户ID
    is_deleted = Column(Boolean, server_default=text('0'), nullable=False, index=True)
    
    # 关系
    raw_answers = relationship("RawAnswer", back_populates="question", cascade="all, delete-orphan", lazy="selectin")
    expert_answers = relationship("ExpertAnswer", back_populates="question", cascade="all, delete-orphan", lazy="selectin")
    tags = relationship("Tag", secondary="RawQuestionTagRecords", back_populates="raw_questions")
    
    # 多对多关系记录
    std_question_records = relationship("StdQuestionRawQuestionRecord", back_populates="raw_question", cascade="all, delete-orphan")