from sqlalchemy.orm import Session, selectinload
from app import models, schemas
from typing import List, Optional
from datetime import datetime

def get_std_answer(db: Session, answer_id: int, include_deleted: bool = False) -> Optional[models.StdAnswer]:
    query = db.query(models.StdAnswer).options(
        selectinload(models.StdAnswer.std_question),
        selectinload(models.StdAnswer.scoring_points.and_(models.StdAnswerScoringPoint.is_valid == True)),
    ).filter(models.StdAnswer.id == answer_id)
    
    if not include_deleted:
        query = query.filter(models.StdAnswer.is_valid == True)
    
    return query.first()

def get_std_answers_count(db: Session, include_deleted: bool = False, deleted_only: bool = False) -> int:
    """获取标准答案总数"""
    query = db.query(models.StdAnswer)
    
    if deleted_only:
        query = query.filter(models.StdAnswer.is_valid == False)
    elif not include_deleted:
        query = query.filter(models.StdAnswer.is_valid == True)
    
    return query.count()

def get_std_answers_paginated(db: Session, skip: int = 0, limit: int = 10, include_deleted: bool = False, deleted_only: bool = False):
    """获取分页的标准答案数据和元数据"""
    from ..schemas.common import PaginatedResponse
    
    # 获取总数
    total = get_std_answers_count(db, include_deleted, deleted_only)    # 获取数据
    query = db.query(models.StdAnswer).options(
        selectinload(models.StdAnswer.std_question),
        selectinload(models.StdAnswer.scoring_points.and_(models.StdAnswerScoringPoint.is_valid == True)),
    ).order_by(models.StdAnswer.id.asc())
    
    if deleted_only:
        query = query.filter(models.StdAnswer.is_valid == False)
    elif not include_deleted:
        query = query.filter(models.StdAnswer.is_valid == True)
    
    answers = query.offset(skip).limit(limit).all()
    
    # 计算分页信息
    current_page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    
    return PaginatedResponse(
        data=answers,
        total=total,
        page=current_page,
        per_page=limit,
        pages=total_pages,
        has_next=skip + limit < total,
        has_prev=skip > 0
    )

def set_std_answer_deleted_status(db: Session, answer_id: int, deleted_status: bool) -> Optional[models.StdAnswer]:
    db_answer = db.query(models.StdAnswer).filter(models.StdAnswer.id == answer_id).first()
    if db_answer:
        db_answer.is_valid = not deleted_status  # StdAnswer uses is_valid instead of is_deleted
        db.commit()
        db.refresh(db_answer)
        return db_answer
    return None

def set_multiple_std_answers_deleted_status(db: Session, answer_ids: List[int], deleted_status: bool) -> int:
    affected_rows = db.query(models.StdAnswer).filter(
        models.StdAnswer.id.in_(answer_ids)
    ).update({models.StdAnswer.is_valid: not deleted_status}, synchronize_session=False)
    db.commit()
    return affected_rows

def force_delete_std_answer(db: Session, answer_id: int) -> bool:
    """永久删除标准答案"""
    try:
        # 首先删除相关的评分点
        db.query(models.StdAnswerScoringPoint).filter(
            models.StdAnswerScoringPoint.std_answer_id == answer_id
        ).delete(synchronize_session=False)
        
        # 删除标准答案
        db.query(models.StdAnswer).filter(models.StdAnswer.id == answer_id).delete(synchronize_session=False)
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error force deleting std answer {answer_id}: {e}")
        return False

def create_std_answer(db: Session, answer: schemas.StdAnswerCreate) -> models.StdAnswer:
    """创建标准回答"""
    db_answer = models.StdAnswer(
        std_question_id=answer.std_question_id,
        answer=answer.answer,
        created_by=answer.created_by,
        version=answer.version or 1,
        previous_version_id=answer.previous_version_id
    )
    
    db.add(db_answer)
    db.flush()  # 获取ID
    
    # 更新原始回答的引用关系
    if answer.referenced_raw_answer_ids:
        db.query(models.RawAnswer).filter(
            models.RawAnswer.id.in_(answer.referenced_raw_answer_ids)
        ).update({models.RawAnswer.referenced_by_std_answer_id: db_answer.id}, synchronize_session=False)
    
    # 更新专家回答的引用关系
    if answer.referenced_expert_answer_ids:
        db.query(models.ExpertAnswer).filter(
            models.ExpertAnswer.id.in_(answer.referenced_expert_answer_ids)
        ).update({models.ExpertAnswer.referenced_by_std_answer_id: db_answer.id}, synchronize_session=False)
    
    # 创建评分点
    for scoring_point_data in answer.scoring_points:
        db_scoring_point = models.StdAnswerScoringPoint(
            std_answer_id=db_answer.id,
            scoring_point_text=scoring_point_data.scoring_point_text,
            point_order=scoring_point_data.point_order,
            created_by=scoring_point_data.created_by
        )
        db.add(db_scoring_point)
    
    db.commit()
    db.refresh(db_answer)
    return db_answer

def update_std_answer(db: Session, answer_id: int, answer: schemas.StdAnswerUpdate) -> Optional[models.StdAnswer]:
    """更新标准回答"""
    db_answer = db.query(models.StdAnswer).filter(models.StdAnswer.id == answer_id).first()
    if not db_answer:
        return None
    
    # 更新基本字段
    update_data = answer.dict(exclude_unset=True, exclude={'scoring_points', 'referenced_raw_answer_ids', 'referenced_expert_answer_ids'})
    for field, value in update_data.items():
        setattr(db_answer, field, value)
    
    # 更新原始回答的引用关系
    if answer.referenced_raw_answer_ids is not None:
        # 清除旧的引用
        db.query(models.RawAnswer).filter(
            models.RawAnswer.referenced_by_std_answer_id == answer_id
        ).update({models.RawAnswer.referenced_by_std_answer_id: None}, synchronize_session=False)
        
        # 设置新的引用
        if answer.referenced_raw_answer_ids:
            db.query(models.RawAnswer).filter(
                models.RawAnswer.id.in_(answer.referenced_raw_answer_ids)
            ).update({models.RawAnswer.referenced_by_std_answer_id: answer_id}, synchronize_session=False)
    
    # 更新专家回答的引用关系
    if answer.referenced_expert_answer_ids is not None:
        # 清除旧的引用
        db.query(models.ExpertAnswer).filter(
            models.ExpertAnswer.referenced_by_std_answer_id == answer_id
        ).update({models.ExpertAnswer.referenced_by_std_answer_id: None}, synchronize_session=False)
        
        # 设置新的引用
        if answer.referenced_expert_answer_ids:
            db.query(models.ExpertAnswer).filter(
                models.ExpertAnswer.id.in_(answer.referenced_expert_answer_ids)
            ).update({models.ExpertAnswer.referenced_by_std_answer_id: answer_id}, synchronize_session=False)
    
    # 如果提供了评分点，更新评分点
    if answer.scoring_points is not None:
        # 删除现有评分点
        db.query(models.StdAnswerScoringPoint).filter(
            models.StdAnswerScoringPoint.std_answer_id == answer_id
        ).delete(synchronize_session=False)
        
        # 创建新的评分点
        for scoring_point_data in answer.scoring_points:
            db_scoring_point = models.StdAnswerScoringPoint(
                std_answer_id=answer_id,
                scoring_point_text=scoring_point_data.scoring_point_text,
                point_order=scoring_point_data.point_order,
                created_by=scoring_point_data.created_by
            )
            db.add(db_scoring_point)
    
    db.commit()
    db.refresh(db_answer)
    return db_answer
