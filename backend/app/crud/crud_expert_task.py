from sqlalchemy.orm import Session, joinedload
from app.models.expert_task import ExpertTask
from app.models.user import User
from app.schemas.expert_task import ExpertTaskCreate, ExpertTaskUpdate
from typing import List, Optional

def create_expert_task(db: Session, task_data: ExpertTaskCreate, expert_id: int) -> ExpertTask:
    """创建专家任务"""
    # 首先验证邀请码是否存在
    admin = db.query(User).filter(User.invite_code == task_data.invite_code).first()
    if not admin:
        raise ValueError("无效的邀请码")
    
    # 检查是否已经存在相同的任务
    existing_task = db.query(ExpertTask).filter(
        ExpertTask.expert_id == expert_id,
        ExpertTask.admin_id == admin.id,
        ExpertTask.is_active == True
    ).first()
    
    if existing_task:
        raise ValueError("您已经接受了该管理员的任务")
    
    db_task = ExpertTask(
        expert_id=expert_id,
        admin_id=admin.id,
        invite_code=task_data.invite_code,
        task_name=task_data.task_name or f"{admin.username}的问题池",
        description=task_data.description,
        is_active=True
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_expert_tasks(db: Session, expert_id: int, skip: int = 0, limit: int = 100) -> List[ExpertTask]:
    """获取专家的任务列表"""
    return db.query(ExpertTask).options(
        joinedload(ExpertTask.expert),
        joinedload(ExpertTask.admin)
    ).filter(
        ExpertTask.expert_id == expert_id,
        ExpertTask.is_active == True
    ).offset(skip).limit(limit).all()

def get_expert_task(db: Session, task_id: int, expert_id: int) -> Optional[ExpertTask]:
    """获取单个专家任务"""
    return db.query(ExpertTask).options(
        joinedload(ExpertTask.expert),
        joinedload(ExpertTask.admin)
    ).filter(
        ExpertTask.id == task_id,
        ExpertTask.expert_id == expert_id,
        ExpertTask.is_active == True
    ).first()

def update_expert_task(db: Session, task_id: int, expert_id: int, task_update: ExpertTaskUpdate) -> Optional[ExpertTask]:
    """更新专家任务"""
    task = get_expert_task(db, task_id, expert_id)
    if not task:
        return None
    
    for field, value in task_update.dict(exclude_unset=True).items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    return task

def delete_expert_task(db: Session, task_id: int, expert_id: int) -> bool:
    """删除（软删除）专家任务"""
    task = get_expert_task(db, task_id, expert_id)
    if not task:
        return False
    
    task.is_active = False
    db.commit()
    return True

def get_admin_by_invite_code(db: Session, invite_code: str) -> Optional[User]:
    """根据邀请码获取管理员信息"""
    return db.query(User).filter(User.invite_code == invite_code).first()
