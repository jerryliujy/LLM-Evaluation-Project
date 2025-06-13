from sqlalchemy import Column, Integer, Text, DateTime, String, Boolean, ForeignKey, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Dataset(Base):
    __tablename__ = "Dataset"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  
    description = Column(Text, nullable=False)    
    created_by = Column(Integer, ForeignKey("User.id"), nullable=False)  # 创建者用户ID
    is_public = Column(Boolean, server_default=text('1'))  # 是否公开
    create_time = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    version = Column(Integer, default=1, nullable=False, index=True)
      # 关系
    creator = relationship("User", back_populates="datasets")
    versions = relationship("DatasetVersion", back_populates="dataset")
