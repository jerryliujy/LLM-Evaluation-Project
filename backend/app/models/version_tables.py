from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, text, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base

class DatasetVersionWork(Base):
    """数据集版本工作表 - 管理数据集版本的修改流程"""
    __tablename__ = "DatasetVersionWork"
    __table_args__ = (
        ForeignKeyConstraint(
            ['dataset_id', 'current_version'],
            ['Dataset.id', 'Dataset.version'],
            name='fk_dataset_version_work_dataset'
        ),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=False, index=True)
    current_version = Column(Integer, nullable=False)  # 当前版本号
    target_version = Column(Integer, nullable=False)   # 目标版本号
    work_status = Column(Enum('in_progress', 'completed', 'cancelled', name='work_status_enum'), 
                         nullable=False, server_default=text("'in_progress'"))
    work_description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("User.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    
    # 关系
    version_questions = relationship("VersionStdQuestion", back_populates="version_work", cascade="all, delete-orphan")
    version_answers = relationship("VersionStdAnswer", back_populates="version_work", cascade="all, delete-orphan")
    version_scoring_points = relationship("VersionScoringPoint", back_populates="version_work", cascade="all, delete-orphan")
    version_tags = relationship("VersionTag", back_populates="version_work", cascade="all, delete-orphan")
    
    class Config:
        from_attributes = True

class VersionStdQuestion(Base):
    """版本工作表中的标准问题 - 只记录修改状态"""
    __tablename__ = "VersionStdQuestion"
    
    id = Column(Integer, primary_key=True, index=True)
    version_work_id = Column(Integer, ForeignKey("DatasetVersionWork.id"), nullable=False, index=True)
    original_question_id = Column(Integer, ForeignKey("StdQuestion.id"), nullable=True, index=True)  # 原始问题ID（新增时为NULL）
    is_modified = Column(Boolean, default=False, nullable=False)  # 是否被修改
    is_new = Column(Boolean, default=False, nullable=False)  # 是否是新创建的
    is_deleted = Column(Boolean, default=False, nullable=False)  # 是否被删除
    
    # 修改后的内容（仅当 is_modified=True 或 is_new=True 时有效）
    modified_body = Column(Text, nullable=True)
    modified_question_type = Column(Enum('choice', 'text', name='question_type_enum'), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    version_work = relationship("DatasetVersionWork", back_populates="version_questions")
    original_question = relationship("StdQuestion")
    version_answers = relationship("VersionStdAnswer", back_populates="version_question", cascade="all, delete-orphan")
    version_tags = relationship("VersionTag", back_populates="version_question", cascade="all, delete-orphan")
    
    class Config:
        from_attributes = True

class VersionStdAnswer(Base):
    """版本工作表中的标准答案 - 只记录修改状态"""
    __tablename__ = "VersionStdAnswer"
    
    id = Column(Integer, primary_key=True, index=True)
    version_work_id = Column(Integer, ForeignKey("DatasetVersionWork.id"), nullable=False, index=True)
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
    version_work = relationship("DatasetVersionWork", back_populates="version_answers")
    version_question = relationship("VersionStdQuestion", back_populates="version_answers")
    original_answer = relationship("StdAnswer")
    version_scoring_points = relationship("VersionScoringPoint", back_populates="version_answer", cascade="all, delete-orphan")
    
    class Config:
        from_attributes = True

class VersionScoringPoint(Base):
    """版本工作表中的得分点 - 只记录修改状态"""
    __tablename__ = "VersionScoringPoint"
    
    id = Column(Integer, primary_key=True, index=True)
    version_work_id = Column(Integer, ForeignKey("DatasetVersionWork.id"), nullable=False, index=True)
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
    version_work = relationship("DatasetVersionWork", back_populates="version_scoring_points")
    version_answer = relationship("VersionStdAnswer", back_populates="version_scoring_points")
    original_point = relationship("StdAnswerScoringPoint")
    
    class Config:
        from_attributes = True

class VersionTag(Base):
    """版本工作表中的标签 - 记录版本中问题的标签状态"""
    __tablename__ = "VersionTag"
    
    id = Column(Integer, primary_key=True, index=True)
    version_work_id = Column(Integer, ForeignKey("DatasetVersionWork.id"), nullable=False, index=True)
    version_question_id = Column(Integer, ForeignKey("VersionStdQuestion.id"), nullable=False, index=True)
    tag_label = Column(String(100), ForeignKey("Tag.label"), nullable=False, index=True)    
    is_deleted = Column(Boolean, server_default=text('0'), nullable=False)  # 是否被删除
    is_new = Column(Boolean, server_default=text('0'), nullable=False)  # 是否是新增的标签
    
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    
    # 关系
    version_work = relationship("DatasetVersionWork", back_populates="version_tags")
    version_question = relationship("VersionStdQuestion", back_populates="version_tags")
    tag = relationship("Tag")
    
    class Config:
        from_attributes = True
