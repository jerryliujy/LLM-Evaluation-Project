from sqlalchemy.orm import Session
from app import models, schemas
from typing import List, Optional

def get_raw_answer(db: Session, answer_id: int, include_deleted: bool = False) -> Optional[models.RawAnswer]:
    query = db.query(models.RawAnswer).filter(models.RawAnswer.id == answer_id)
    if not include_deleted:
        query = query.filter(models.RawAnswer.is_deleted == False)
    return query.first()

def get_raw_answers_count(db: Session, include_deleted: bool = False, deleted_only: bool = False) -> int:
    """获取原始答案总数"""
    query = db.query(models.RawAnswer)
    
    if deleted_only:
        query = query.filter(models.RawAnswer.is_deleted == True)
    elif not include_deleted:
        query = query.filter(models.RawAnswer.is_deleted == False)
    
    return query.count()

def get_raw_answers_paginated(db: Session, skip: int = 0, limit: int = 10, include_deleted: bool = False, deleted_only: bool = False):
    """获取分页的原始答案数据和元数据"""
    query = db.query(models.RawAnswer)
    
    if deleted_only:
        query = query.filter(models.RawAnswer.is_deleted == True)
    elif not include_deleted:
        query = query.filter(models.RawAnswer.is_deleted == False)
    
    answers = query.order_by(models.RawAnswer.id.asc()).offset(skip).limit(limit).all()
    total = get_raw_answers_count(db, include_deleted, deleted_only)
    
    return {
        "data": answers,
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit,
        "total_pages": (total + limit - 1) // limit,
        "has_next": skip + limit < total,
        "has_prev": skip > 0
    }

# create_raw_answer
def create_raw_answer(db: Session, answer: schemas.RawAnswerCreate) -> models.RawAnswer:
    """创建新的原始回答"""
    answer_data = answer.dict()
    
    if "is_deleted" not in answer_data:
        answer_data["is_deleted"] = False
    
    db_answer = models.RawAnswer(**answer_data)
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer

def set_raw_answer_deleted_status(db: Session, answer_id: int, deleted_status: bool) -> Optional[models.RawAnswer]:
    db_answer = db.query(models.RawAnswer).filter(models.RawAnswer.id == answer_id).first()
    if not db_answer:
        return None
        
    # 如果是恢复操作，需要检查关联的问题是否已恢复
    if not deleted_status:  # 恢复操作
        # 检查关联的问题状态
        question = db.query(models.RawQuestion).filter(
            models.RawQuestion.id == db_answer.question_id
        ).first()
        
        if not question or question.is_deleted:
            # 关联的问题不存在或已被删除，不能恢复回答
            raise ValueError("Cannot restore answer: associated question is deleted or does not exist")
    
    db_answer.is_deleted = deleted_status
    db.commit()
    db.refresh(db_answer)
    return db_answer
    
def set_multiple_raw_answers_deleted_status(db: Session, answer_ids: List[int], deleted_status: bool) -> int:
    if not answer_ids: 
        return 0
        
    # 如果是恢复操作，需要检查每个回答关联的问题状态
    if not deleted_status:  # 恢复操作
        # 获取所有回答及其关联的问题
        answers_with_questions = db.query(models.RawAnswer, models.RawQuestion).join(
            models.RawQuestion, models.RawAnswer.question_id == models.RawQuestion.id
        ).filter(models.RawAnswer.id.in_(answer_ids)).all()
        
        # 检查是否有关联的问题被删除
        deleted_questions = [
            (answer.id, question.id) for answer, question in answers_with_questions 
            if question.is_deleted
        ]
        
        if deleted_questions:
            deleted_question_ids = [q_id for _, q_id in deleted_questions]
            raise ValueError(f"Cannot restore answers: associated questions {deleted_question_ids} are deleted")
    
    num_updated = db.query(models.RawAnswer).filter(models.RawAnswer.id.in_(answer_ids)).update({"is_deleted": deleted_status}, synchronize_session=False)
    db.commit()
    return num_updated

def force_delete_raw_answer(db: Session, answer_id: int) -> bool:
    """永久删除原始答案（物理删除）"""
    try:
        # 删除答案（原始答案通常没有其他依赖关系）
        num_deleted = db.query(models.RawAnswer).filter(models.RawAnswer.id == answer_id).delete(synchronize_session=False)
        db.commit()
        return num_deleted > 0
    except Exception as e:
        db.rollback()
        print(f"Error in force_delete_raw_answer: {e}")
        return False

def update_raw_answer(db: Session, answer_id: int, answer_update: schemas.RawAnswerBase) -> Optional[models.RawAnswer]:
    db_answer = db.query(models.RawAnswer).filter(models.RawAnswer.id == answer_id, models.RawAnswer.is_deleted == False).first()
    if not db_answer:
        return None
    db_answer.answer = answer_update.answer
    db_answer.upvotes = answer_update.upvotes
    db_answer.answered_by = answer_update.answered_by
    db_answer.answered_at = answer_update.answered_at
    db.commit()
    db.refresh(db_answer)
    return db_answer