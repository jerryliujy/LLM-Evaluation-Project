from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, ForeignKeyConstraint
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class StdQuestion(Base):
    __tablename__ = "StdQuestion"    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=False, index=True)  # 当前所在的数据集ID
    dataset_version = Column(Integer, nullable=False, default=1, index=True)  # 数据集版本
    raw_question_id = Column(Integer, ForeignKey("RawQuestion.id"), nullable=False, index=True)  # 原始问题ID，必须不能为空
    body = Column(Text, nullable=False)  
    question_type = Column(Enum('choice', 'text', name='question_type_enum'), nullable=False, default='text')
    is_valid = Column(Boolean, server_default=text('1'), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))  
    created_by = Column(Integer, ForeignKey("User.id"), nullable=True, index=True)
    version = Column(Integer, nullable=False, default=1, index=True)
    previous_version_id = Column(Integer, ForeignKey("StdQuestion.id"), nullable=True, index=True)
    
    # 版本管理字段
    original_version_id = Column(Integer, nullable=True, index=True)  # 最初创建时的版本号
    current_version_id = Column(Integer, nullable=True, index=True)   # 当前所在的版本号
    
    # 设置复合外键约束
    __table_args__ = (
        ForeignKeyConstraint(['dataset_id', 'dataset_version'], ['Dataset.id', 'Dataset.version']),
    )
    
    # Relationships
    dataset = relationship("Dataset", 
                         foreign_keys=[dataset_id, dataset_version],
                         primaryjoin="and_(StdQuestion.dataset_id==Dataset.id, StdQuestion.dataset_version==Dataset.version)")
    raw_question = relationship("RawQuestion", foreign_keys=[raw_question_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    previous_version = relationship("StdQuestion", remote_side=[id])
    std_answers = relationship("StdAnswer", back_populates="std_question", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="QuestionTagRecords", back_populates="std_questions")
    
    # 多对多关系记录
    raw_question_records = relationship("StdQuestionRawQuestionRecord", back_populates="std_question", cascade="all, delete-orphan")
