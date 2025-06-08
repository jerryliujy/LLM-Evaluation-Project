from sqlalchemy.orm import Session, selectinload
from app import models, schemas
from typing import List, Optional
from datetime import datetime

def get_std_question(db: Session, question_id: int, include_deleted: bool = False) -> Optional[models.StdQuestion]:
    query = db.query(models.StdQuestion).options(
        selectinload(models.StdQuestion.dataset),
        selectinload(models.StdQuestion.std_answers.and_(models.StdAnswer.is_valid == True)),
        selectinload(models.StdQuestion.tags)
    ).filter(models.StdQuestion.id == question_id)
    
    if not include_deleted:
        query = query.filter(models.StdQuestion.is_valid == True)
    
    return query.first()

def get_std_questions_count(db: Session, include_deleted: bool = False, deleted_only: bool = False) -> int:
    """获取标准问题总数"""
    query = db.query(models.StdQuestion)
    
    if deleted_only:
        query = query.filter(models.StdQuestion.is_valid == False)
    elif not include_deleted:
        query = query.filter(models.StdQuestion.is_valid == True)
    
    return query.count()

def get_std_questions_paginated(db: Session, skip: int = 0, limit: int = 10, include_deleted: bool = False, deleted_only: bool = False):
    """获取分页的标准问题数据和元数据"""
    from ..schemas.common import PaginatedResponse
    
    # 获取总数
    total = get_std_questions_count(db, include_deleted, deleted_only)
    
    # 获取数据
    query = db.query(models.StdQuestion).options(
        selectinload(models.StdQuestion.dataset),
        selectinload(models.StdQuestion.std_answers.and_(models.StdAnswer.is_valid == True)),
        selectinload(models.StdQuestion.tags)
    ).order_by(models.StdQuestion.id.asc())
    
    if deleted_only:
        query = query.filter(models.StdQuestion.is_valid == False)
    elif not include_deleted:
        query = query.filter(models.StdQuestion.is_valid == True)
    
    questions = query.offset(skip).limit(limit).all()
    
    # 计算分页信息
    current_page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    return PaginatedResponse(
        data=questions,
        total=total,
        page=current_page,
        per_page=limit,
        total_pages=total_pages,
        has_next=skip + limit < total,
        has_prev=skip > 0
    )

def set_std_question_deleted_status(db: Session, question_id: int, deleted_status: bool) -> Optional[models.StdQuestion]:
    db_question = db.query(models.StdQuestion).filter(models.StdQuestion.id == question_id).first()
    if db_question:
        db_question.is_valid = not deleted_status  # StdQuestion uses is_valid instead of is_deleted
        db.commit()
        db.refresh(db_question)
        return db_question
    return None

def set_multiple_std_questions_deleted_status(db: Session, question_ids: List[int], deleted_status: bool) -> int:
    affected_rows = db.query(models.StdQuestion).filter(
        models.StdQuestion.id.in_(question_ids)
    ).update({models.StdQuestion.is_valid: not deleted_status}, synchronize_session=False)
    db.commit()
    return affected_rows

def force_delete_std_question(db: Session, question_id: int) -> bool:
    """永久删除标准问题"""
    try:
        # 首先删除相关的标准答案和评分点
        std_answers = db.query(models.StdAnswer).filter(models.StdAnswer.std_question_id == question_id).all()
        for answer in std_answers:
            # 删除评分点
            db.query(models.StdAnswerScoringPoint).filter(
                models.StdAnswerScoringPoint.std_answer_id == answer.id
            ).delete(synchronize_session=False)
            
        # 删除标准答案
        db.query(models.StdAnswer).filter(models.StdAnswer.std_question_id == question_id).delete(synchronize_session=False)
        
        # 删除标准问题
        db.query(models.StdQuestion).filter(models.StdQuestion.id == question_id).delete(synchronize_session=False)
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error force deleting std question {question_id}: {e}")
        return False

def create_std_question(db: Session, question: schemas.StdQuestionCreate) -> models.StdQuestion:
    """创建标准问题，支持嵌套的标准回答"""
    db_question = models.StdQuestion(
        dataset_id=question.dataset_id,
        body=question.body,  # 统一字段名为body
        question_type=question.question_type,
        created_by=question.created_by,
    )
    
    db.add(db_question)
    db.flush()  # 获取question的ID
    
    # 如果提供了std_answer，创建标准回答
    if hasattr(question, 'std_answer') and question.std_answer:
        db_answer = models.StdAnswer(
            std_question_id=db_question.id,
            answer=question.std_answer.answer,
            answered_by=question.std_answer.answered_by,  # 统一字段名为answered_by
        )
        db.add(db_answer)
    
    db.commit()
    db.refresh(db_question)
    return db_question

def update_std_question(db: Session, question_id: int, question: schemas.StdQuestionUpdate) -> Optional[models.StdQuestion]:
    """更新标准问题"""
    db_question = db.query(models.StdQuestion).filter(models.StdQuestion.id == question_id).first()
    if not db_question:
        return None
    
    # 更新问题字段
    update_data = question.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_question, field, value)
    
    db.commit()
    db.refresh(db_question)
    return db_question
