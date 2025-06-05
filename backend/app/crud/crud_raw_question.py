from sqlalchemy.orm import Session, selectinload
from .. import models, schemas
from ..models import RawAnswer, ExpertAnswer
from typing import List, Optional

def get_raw_question(db: Session, question_id: int) -> Optional[models.RawQuestion]:
    return db.query(models.RawQuestion).options(
        selectinload(models.RawQuestion.raw_answers.and_(models.RawAnswer.is_deleted == False)),
        selectinload(models.RawQuestion.expert_answers.and_(models.ExpertAnswer.is_deleted == False)),
        selectinload(models.RawQuestion.tags)  
    ).filter(models.RawQuestion.id == question_id, models.RawQuestion.is_deleted == False).first()

def get_raw_question_including_deleted(db: Session, question_id: int) -> Optional[models.RawQuestion]:
    # Used for restore to get the item even if marked as deleted
    return db.query(models.RawQuestion).options(
        selectinload(models.RawQuestion.raw_answers), # Load all answers for restoration context
        selectinload(models.RawQuestion.expert_answers)
    ).filter(models.RawQuestion.id == question_id).first()


def get_raw_questions(db: Session, skip: int = 0, limit: int = 10) -> List[models.RawQuestion]:
    return db.query(models.RawQuestion).options(
        selectinload(models.RawQuestion.raw_answers.and_(models.RawAnswer.is_deleted == False)),
        selectinload(models.RawQuestion.expert_answers.and_(models.ExpertAnswer.is_deleted == False)),
        selectinload(models.RawQuestion.tags)  
    ).filter(models.RawQuestion.is_deleted == False).order_by(models.RawQuestion.id.asc()).offset(skip).limit(limit).all()

def get_raw_questions_count(db: Session, include_deleted: bool = False, deleted_only: bool = False) -> int:
    """获取原始问题总数"""
    query = db.query(models.RawQuestion)
    
    if deleted_only:
        query = query.filter(models.RawQuestion.is_deleted == True)
    elif not include_deleted:
        query = query.filter(models.RawQuestion.is_deleted == False)
    
    return query.count()

def get_raw_questions_paginated(db: Session, skip: int = 0, limit: int = 10, include_deleted: bool = False, deleted_only: bool = False):
    """获取分页的原始问题数据和元数据"""
    # 获取数据
    query = db.query(models.RawQuestion).options(
        selectinload(models.RawQuestion.raw_answers.and_(models.RawAnswer.is_deleted == False)),
        selectinload(models.RawQuestion.expert_answers.and_(models.ExpertAnswer.is_deleted == False)),
        selectinload(models.RawQuestion.tags)
    )
    
    if deleted_only:
        # 只显示已删除的
        query = query.filter(models.RawQuestion.is_deleted == True)
    elif not include_deleted:
        # 只显示未删除的
        query = query.filter(models.RawQuestion.is_deleted == False)
    # 如果include_deleted=True且deleted_only=False，则显示全部
    
    questions = query.order_by(models.RawQuestion.id.asc()).offset(skip).limit(limit).all()
    
    # 获取总数
    total = get_raw_questions_count(db, include_deleted, deleted_only)
    
    return {
        "data": questions,
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit,
        "total_pages": (total + limit - 1) // limit,
        "has_next": skip + limit < total,
        "has_prev": skip > 0
    }

# create_raw_question (deferred)

def set_raw_question_deleted_status(db: Session, question_id: int, deleted_status: bool) -> Optional[models.RawQuestion]:
    db_question = db.query(models.RawQuestion).filter(models.RawQuestion.id == question_id).first()
    if db_question:
        db_question.is_deleted = deleted_status
        # Note: Cascading soft delete for answers is handled by relationship cascade="all, delete-orphan"
        # if SQLAlchemy is configured for it, or manually:
        # if deleted_status:
        #     for ra in db_question.raw_answers: ra.is_deleted = True
        #     for ca in db_question.crowdsourced_answers: ca.is_deleted = True
        # Else, if restoring, answers might need separate restoration if they were individually deleted.
        # For simplicity, this example assumes deleting a question makes its answers effectively inaccessible
        # unless restored with the question or individually.
        db.commit()
        db.refresh(db_question)
        # For response, reload with filtered answers if it's a restore operation
        if not deleted_status:
             return get_raw_question(db, question_id) # Return with correctly filtered sub-items
        return db_question # For delete, the object state is fine
    return None

def set_multiple_raw_questions_deleted_status(db: Session, question_ids: List[int], deleted_status: bool) -> int:
    if not question_ids: 
        return 0
    num_updated = db.query(models.RawQuestion).filter(models.RawQuestion.id.in_(question_ids)).update({"is_deleted": deleted_status}, synchronize_session=False)
    db.commit()
    return num_updated

def force_delete_raw_question(db: Session, question_id: int) -> bool:
    """永久删除原始问题（物理删除）"""
    try:
        # 获取问题对象以确保存在
        question = db.query(models.RawQuestion).filter(models.RawQuestion.id == question_id).first()
        if not question:
            return False
            
        # 1. 删除标签关联关系（多对多关系）
        # 通过清空relationship来删除关联表中的记录
        question.tags.clear()
        db.flush()  # 确保关联记录被删除
        
        # 2. 删除相关的答案
        db.query(models.RawAnswer).filter(models.RawAnswer.question_id == question_id).delete(synchronize_session=False)
        db.query(models.ExpertAnswer).filter(models.ExpertAnswer.question_id == question_id).delete(synchronize_session=False)
        
        # 3. 删除标准问题
        from ..models.std_question import StdQuestion
        db.query(StdQuestion).filter(StdQuestion.raw_question_id == question_id).delete(synchronize_session=False)
        
        # 4. 最后删除问题本身
        num_deleted = db.query(models.RawQuestion).filter(models.RawQuestion.id == question_id).delete(synchronize_session=False)
        
        db.commit()
        return num_deleted > 0
    except Exception as e:
        db.rollback()
        print(f"Error in force_delete_raw_question: {e}")  # 添加日志输出以便调试
        return False