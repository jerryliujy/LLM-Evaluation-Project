from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base

class DatasetVersion(Base):
    __tablename__ = "DatasetVersion"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("Dataset.id"), nullable=False)  # 原始数据库ID
    name = Column(String(255), nullable=False)  # 版本名称
    description = Column(Text, nullable=True)  # 版本描述
    version_number = Column(String(50), nullable=False)  # 版本号
    is_committed = Column(Boolean, default=False, nullable=False)  # 是否已提交
    is_public = Column(Boolean, default=False, nullable=False)  # 是否公开
    created_by = Column(Integer, ForeignKey("User.id"), nullable=False)  # 创建者
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    committed_at = Column(DateTime(timezone=True), nullable=True)  # 提交时间
    
    # 关系
    dataset = relationship("Dataset", back_populates="versions")
    created_by_user = relationship("User", foreign_keys=[created_by])
    version_questions = relationship("VersionStdQuestion", back_populates="version")
    
    class Config:
        from_attributes = True
