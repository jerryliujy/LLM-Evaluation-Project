from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base

class VersionStdQuestion(Base):
    """版本工作表中的标准问题 - 只记录修改状态"""
    __tablename__ = "VersionStdQuestion"
    
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("DatasetVersion.id"), nullable=False, index=True)
    original_question_id = Column(Integer, ForeignKey("StdQuestion.id"), nullable=False, index=True)  # 原始问题ID
    is_modified = Column(Boolean, default=False, nullable=False)  # 是否被修改
    is_new = Column(Boolean, default=False, nullable=False)  # 是否是新创建的
    is_deleted = Column(Boolean, default=False, nullable=False)  # 是否被删除
    
    # 修改后的内容（仅当 is_modified=True 时有效）
    modified_body = Column(Text, nullable=True)
    modified_question_type = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # 关系
    version = relationship("DatasetVersion")
    original_question = relationship("StdQuestion")
    version_answers = relationship("VersionStdAnswer", back_populates="version_question", cascade="all, delete-orphan")
    
    class Config:
        from_attributes = True

class VersionStdAnswer(Base):
    """版本工作表中的标准答案 - 只记录修改状态"""
    __tablename__ = "VersionStdAnswer"
    
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("DatasetVersion.id"), nullable=False, index=True)
    version_question_id = Column(Integer, ForeignKey("VersionStdQuestion.id"), nullable=False, index=True)
    original_answer_id = Column(Integer, ForeignKey("StdAnswer.id"), nullable=True, index=True)  # 可能为空（新增的答案）
    is_modified = Column(Boolean, default=False, nullable=False)  # 是否被修改
    is_deleted = Column(Boolean, default=False, nullable=False)  # 是否被删除
    is_new = Column(Boolean, default=True, nullable=False)  # 是否是新增的答案
    
    # 修改后的内容（仅当 is_modified=True 或 is_new=True 时有效）
    modified_answer = Column(Text, nullable=True)
    modified_answered_by = Column(Integer, ForeignKey("User.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    version_question = relationship("VersionStdQuestion", back_populates="version_answers")
    original_answer = relationship("StdAnswer")
    version_scoring_points = relationship("VersionScoringPoint", back_populates="version_answer", cascade="all, delete-orphan")
    
    class Config:
        from_attributes = True

class VersionScoringPoint(Base):
    """版本工作表中的得分点 - 只记录修改状态"""
    __tablename__ = "VersionScoringPoint"
    
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("DatasetVersion.id"), nullable=False, index=True)
    version_answer_id = Column(Integer, ForeignKey("VersionStdAnswer.id"), nullable=False, index=True)
    original_point_id = Column(Integer, ForeignKey("StdAnswerScoringPoint.id"), nullable=True, index=True)  # 可能为空（新增的得分点）
    is_modified = Column(Boolean, default=False, nullable=False)  # 是否被修改
    is_deleted = Column(Boolean, default=False, nullable=False)  # 是否被删除
    is_new = Column(Boolean, default=True, nullable=False)  # 是否是新增的得分点
    
    # 修改后的内容（仅当 is_modified=True 或 is_new=True 时有效）
    modified_answer = Column(Text, nullable=True)
    modified_point_order = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())    
    # 关系
    version_answer = relationship("VersionStdAnswer", back_populates="version_scoring_points")
    original_point = relationship("StdAnswerScoringPoint")
    
    class Config:
        from_attributes = True
