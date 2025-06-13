from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class ExpertTask(Base):
    """专家任务 - 记录专家通过邀请码访问的数据库管理者任务"""
    __tablename__ = "ExpertTask"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    expert_id = Column(Integer, ForeignKey("User.id"), nullable=False, index=True)  # 专家ID
    admin_id = Column(Integer, ForeignKey("User.id"), nullable=False, index=True)   # 数据库管理者ID    invite_code = Column(String(36), nullable=False, index=True)                    # 使用的邀请码
    task_name = Column(String(255), nullable=True)                                  # 任务名称（可选）
    description = Column(Text, nullable=True)                                       # 任务描述（可选）
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    is_active = Column(Boolean, nullable=False, server_default=text('1'))                       # 任务是否激活
    
    # 关系
    expert = relationship("User", foreign_keys=[expert_id], backref="expert_tasks")
    admin = relationship("User", foreign_keys=[admin_id], backref="assigned_tasks")
