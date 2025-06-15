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
    # raw_question_id 字段已移除，改为通过关系表 StdQuestionRawQuestionRecord 关联
    body = Column(Text, nullable=False)  
    question_type = Column(Enum('choice', 'text', name='question_type_enum'), nullable=False, default='text')
    is_valid = Column(Boolean, server_default=text('1'), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))  
    created_by = Column(Integer, ForeignKey("User.id"), nullable=True, index=True)
    version = Column(Integer, nullable=False, default=1, index=True)
    previous_version_id = Column(Integer, ForeignKey("StdQuestion.id"), nullable=True, index=True)
    # 版本管理字段
    original_version_id = Column(Integer, nullable=False, index=True)  # 最初创建时的版本号
    current_version_id = Column(Integer, nullable=False, index=True)   # 当前所在的版本号
    # 复合外键约束
    __table_args__ = (
        ForeignKeyConstraint(['dataset_id', 'current_version_id'], ['Dataset.id', 'Dataset.version']),
    )
    
    # Relationships
    dataset = relationship("Dataset", foreign_keys=[dataset_id, current_version_id])
    # raw_question 关系已移除，改为通过 raw_question_records 关联
    created_by_user = relationship("User", foreign_keys=[created_by])
    previous_version = relationship("StdQuestion", remote_side=[id])
    std_answers = relationship("StdAnswer", back_populates="std_question", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="QuestionTagRecords", back_populates="std_questions")
    
    # 多对多关系记录
    raw_question_records = relationship("StdQuestionRawQuestionRecord", back_populates="std_question", cascade="all, delete-orphan")
