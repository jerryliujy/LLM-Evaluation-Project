from sqlalchemy import Column, Integer, Text, DateTime, String, Boolean, ForeignKey, text, PrimaryKeyConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Dataset(Base):
    __tablename__ = "Dataset"

    id = Column(Integer, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1, index=True)
    name = Column(String(255), nullable=False)  
    description = Column(Text, nullable=False)    
    created_by = Column(Integer, ForeignKey("User.id"), nullable=False)  # 创建者用户ID
    is_public = Column(Boolean, server_default=text('0'))  # 是否公开，默认为私有
    create_time = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    
    # 设置复合主键
    __table_args__ = (
        PrimaryKeyConstraint('id', 'version'),
    )
    
    creator = relationship("User", back_populates="datasets")
