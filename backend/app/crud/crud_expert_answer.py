from sqlalchemy.orm import Session, selectinload
from .. import models, schemas
from typing import List, Optional

def get_expert_answer(db: Session, answer_id: int, include_deleted: bool = False) -> Optional[models.ExpertAnswer]:
    query = db.query(models.ExpertAnswer).filter(models.ExpertAnswer.id == answer_id)
    if not include_deleted:
        query = query.filter(models.ExpertAnswer.is_deleted == False)
    return query.first()

def get_expert_answers_by_author(db: Session, author_id: int, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[models.ExpertAnswer]:
    """获取指定作者的专家回答列表"""
    query = db.query(models.ExpertAnswer).filter(
        models.ExpertAnswer.answered_by == author_id
    )
    if not include_deleted:
        query = query.filter(models.ExpertAnswer.is_deleted == False)
    return query.order_by(models.ExpertAnswer.answered_at.desc()).offset(skip).limit(limit).all()

def create_expert_answer(db: Session, answer: schemas.ExpertAnswerCreate, author_id: int) -> models.ExpertAnswer:
    """创建专家回答"""
    db_answer = models.ExpertAnswer(
        question_id=answer.question_id,
        answer=answer.answer,
        answered_by=author_id
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer

def update_expert_answer(db: Session, answer_id: int, answer_update: schemas.ExpertAnswerUpdate) -> Optional[models.ExpertAnswer]:
    """更新专家回答"""
    db_answer = db.query(models.ExpertAnswer).filter(models.ExpertAnswer.id == answer_id).first()
    if not db_answer:
        return None
      # 更新基本字段
    if answer_update.answer is not None:
        db_answer.answer = answer_update.answer
    
    db.commit()
    db.refresh(db_answer)
    return db_answer

def set_expert_answer_deleted_status(db: Session, answer_id: int, deleted_status: bool) -> Optional[models.ExpertAnswer]:
    db_answer = db.query(models.ExpertAnswer).filter(models.ExpertAnswer.id == answer_id).first()
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
            raise ValueError("Cannot restore expert answer: associated question is deleted or does not exist")
    
    db_answer.is_deleted = deleted_status
    db.commit()
    db.refresh(db_answer)
    return db_answer

def set_multiple_expert_answers_deleted_status(db: Session, answer_ids: List[int], deleted_status: bool) -> int:
    if not answer_ids: 
        return 0
        
    # 如果是恢复操作，需要检查每个回答关联的问题状态
    if not deleted_status:  # 恢复操作
        # 获取所有回答及其关联的问题
        answers_with_questions = db.query(models.ExpertAnswer, models.RawQuestion).join(
            models.RawQuestion, models.ExpertAnswer.question_id == models.RawQuestion.id
        ).filter(models.ExpertAnswer.id.in_(answer_ids)).all()
        
        # 检查是否有关联的问题被删除
        deleted_questions = [
            (answer.id, question.id) for answer, question in answers_with_questions 
            if question.is_deleted
        ]
        
        if deleted_questions:
            deleted_question_ids = [q_id for _, q_id in deleted_questions]
            raise ValueError(f"Cannot restore expert answers: associated questions {deleted_question_ids} are deleted")
    
    num_updated = db.query(models.ExpertAnswer).filter(models.ExpertAnswer.id.in_(answer_ids)).update({"is_deleted": deleted_status}, synchronize_session=False)
    db.commit()
    return num_updated

def get_expert_answers_count(db: Session, include_deleted: bool = False, deleted_only: bool = False) -> int:
    """获取专家答案总数"""
    query = db.query(models.ExpertAnswer)
    
    if deleted_only:
        query = query.filter(models.ExpertAnswer.is_deleted == True)
    elif not include_deleted:
        query = query.filter(models.ExpertAnswer.is_deleted == False)
    
    return query.count()

def get_expert_answers_paginated(db: Session, skip: int = 0, limit: int = 10, include_deleted: bool = False, deleted_only: bool = False):
    """获取分页的专家答案数据和元数据"""
    query = db.query(models.ExpertAnswer)
    
    if deleted_only:
        query = query.filter(models.ExpertAnswer.is_deleted == True)
    elif not include_deleted:
        query = query.filter(models.ExpertAnswer.is_deleted == False)
    
    answers = query.order_by(models.ExpertAnswer.id.asc()).offset(skip).limit(limit).all()
    total = get_expert_answers_count(db, include_deleted, deleted_only)
    
    return {
        "data": answers,
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit,
        "total_pages": (total + limit - 1) // limit,
        "has_next": skip + limit < total,
        "has_prev": skip > 0
    }

def force_delete_expert_answer(db: Session, answer_id: int) -> bool:
    """永久删除专家答案（物理删除）"""
    try:
        # 删除答案（专家答案通常没有其他依赖关系）
        num_deleted = db.query(models.ExpertAnswer).filter(models.ExpertAnswer.id == answer_id).delete(synchronize_session=False)
        db.commit()
        return num_deleted > 0
    except Exception as e:
        db.rollback()
        print(f"Error in force_delete_expert_answer: {e}")
        return False