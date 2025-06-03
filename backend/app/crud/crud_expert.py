from sqlalchemy.orm import Session
from .. import models
from ..schemas.expert import ExpertCreate
from typing import Optional, List

def create_expert(db: Session, expert: ExpertCreate) -> models.Expert:
    """创建新专家"""
    db_expert = models.Expert(
        name=expert.name,
        email=expert.email,
        password=expert.password or "default_password",  # 简单密码处理
        is_deleted=False
    )
    db.add(db_expert)
    db.commit()
    db.refresh(db_expert)
    return db_expert

def get_expert(db: Session, expert_id: int) -> Optional[models.Expert]:
    """获取专家信息"""
    return db.query(models.Expert).filter(
        models.Expert.id == expert_id,
        models.Expert.is_deleted == False
    ).first()

def get_all_experts(db: Session, include_deleted: bool = False) -> List[models.Expert]:
    """获取所有专家列表"""
    query = db.query(models.Expert)
    if not include_deleted:
        query = query.filter(models.Expert.is_deleted == False)
    return query.order_by(models.Expert.created_at.desc()).all()

def get_expert_by_email(db: Session, email: str) -> Optional[models.Expert]:
    """根据邮箱获取专家"""
    return db.query(models.Expert).filter(
        models.Expert.email == email,
        models.Expert.is_deleted == False
    ).first()

def verify_expert_login(db: Session, email: str, password: str) -> Optional[models.Expert]:
    """验证专家登录"""
    expert = db.query(models.Expert).filter(
        models.Expert.email == email,
        models.Expert.is_deleted == False
    ).first()
    
    if expert and expert.password == password:  # 简化的密码验证
        return expert
    return None

def set_expert_deleted_status(db: Session, expert_id: int, deleted_status: bool) -> Optional[models.Expert]:
    db_expert = db.query(models.Expert).filter(models.Expert.id == expert_id).first()
    if db_expert:
        db_expert.is_deleted = deleted_status
        db.commit()
        db.refresh(db_expert)
    return db_expert