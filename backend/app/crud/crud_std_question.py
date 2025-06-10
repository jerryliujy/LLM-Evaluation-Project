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

def get_std_questions_paginated(
    db: Session, 
    skip: int = 0, 
    limit: int = 10, 
    include_deleted: bool = False, 
    deleted_only: bool = False,
    dataset_id: Optional[int] = None,
    search_query: Optional[str] = None,
    tag_filter: Optional[str] = None,
    question_type_filter: Optional[str] = None,
    scoring_points_filter: Optional[str] = None
):
    """获取分页的标准问题数据和元数据，支持搜索和筛选"""
    from ..schemas.common import PaginatedResponse
    from sqlalchemy import and_, or_
    
    # 构建基础查询
    query = db.query(models.StdQuestion).options(
        selectinload(models.StdQuestion.current_dataset),
        selectinload(models.StdQuestion.std_answers.and_(models.StdAnswer.is_valid == True)),
        selectinload(models.StdQuestion.tags)
    )
    
    # 应用删除状态过滤
    if deleted_only:
        query = query.filter(models.StdQuestion.is_valid == False)
    elif not include_deleted:
        query = query.filter(models.StdQuestion.is_valid == True)
    # 应用数据集过滤（使用范围查询代替直接匹配）
    if dataset_id is not None:
        query = query.filter(
            and_(
                models.StdQuestion.original_dataset_id <= dataset_id,
                models.StdQuestion.current_dataset_id >= dataset_id
            )
        )
    
    # 应用搜索查询
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(models.StdQuestion.body.ilike(search_term))
    
    # 应用标签过滤
    if tag_filter:
        from ..models.tag import Tag
        query = query.join(models.StdQuestion.tags).filter(Tag.label.ilike(f"%{tag_filter}%"))
      # 应用问题类型过滤
    if question_type_filter:
        query = query.filter(models.StdQuestion.question_type == question_type_filter)
    
    # 应用得分点筛选
    if scoring_points_filter:
        if scoring_points_filter == "has_scoring_points":
            # 筛选有得分点的问题：标准问题有标准答案，且标准答案有有效的得分点
            query = query.join(models.StdAnswer).join(models.StdAnswerScoringPoint).filter(
                and_(
                    models.StdAnswer.is_valid == True,
                    models.StdAnswerScoringPoint.is_valid == True
                )
            )
        elif scoring_points_filter == "no_scoring_points":
            # 筛选无得分点的问题：要么没有标准答案，要么标准答案没有有效的得分点
            subquery = db.query(models.StdQuestion.id).join(models.StdAnswer).join(models.StdAnswerScoringPoint).filter(
                and_(
                    models.StdAnswer.is_valid == True,
                    models.StdAnswerScoringPoint.is_valid == True
                )
            ).subquery()
            query = query.filter(~models.StdQuestion.id.in_(subquery))
    
    # 去重（如果有标签联接或得分点联接的话）
    if tag_filter or scoring_points_filter == "has_scoring_points":
        query = query.distinct()
    
    # 获取总数
    total = query.count()
    
    # 获取分页数据
    questions = query.order_by(models.StdQuestion.id.asc()).offset(skip).limit(limit).all()
      # 转换为字典格式以避免序列化问题
    questions_data = []
    for question in questions:        
        question_dict = {
            "id": question.id,
            "original_dataset_id": question.original_dataset_id,
            "current_dataset_id": question.current_dataset_id,
            "body": question.body,
            "question_type": question.question_type,
            "created_by": question.created_by,
            "created_at": question.created_at,
            "is_valid": question.is_valid,
            "previous_version_id": question.previous_version_id,            
            "dataset": {
                "id": question.current_dataset.id,
                "name": question.current_dataset.name,
                "description": question.current_dataset.description
            } if question.current_dataset else None,
            "tags": [tag.label for tag in question.tags] if question.tags else [],            
            "std_answers": [
                {
                    "id": answer.id,
                    "answer": answer.answer,
                    "answered_by": answer.answered_by,
                    "is_valid": answer.is_valid,
                    "scoring_points": [
                        {
                            "id": sp.id,
                            "answer": sp.answer,
                            "point_order": sp.point_order,
                            "is_valid": sp.is_valid
                        } for sp in answer.scoring_points if sp.is_valid
                    ] if answer.scoring_points else []
                } for answer in question.std_answers if answer.is_valid
            ] if question.std_answers else []
        }
    
        questions_data.append(question_dict)
    
    # 计算分页信息
    current_page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    return PaginatedResponse(
        data=questions_data,
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
        
        # 级联删除/恢复关联的标准答案
        if deleted_status:  # 删除操作 - 级联删除关联的标准答案
            # 软删除所有关联的标准答案
            db.query(models.StdAnswer).filter(
                models.StdAnswer.std_question_id == question_id,
                models.StdAnswer.is_valid == True
            ).update({"is_valid": False}, synchronize_session=False)
        else:  # 恢复操作 - 级联恢复关联的标准答案
            # 恢复所有关联的标准答案
            db.query(models.StdAnswer).filter(
                models.StdAnswer.std_question_id == question_id,
                models.StdAnswer.is_valid == False
            ).update({"is_valid": True}, synchronize_session=False)
        
        db.commit()
        db.refresh(db_question)
        return db_question
    return None

def set_multiple_std_questions_deleted_status(db: Session, question_ids: List[int], deleted_status: bool) -> int:
    if not question_ids:
        return 0
    
    # 级联删除/恢复关联的标准答案
    if deleted_status:  # 删除操作 - 级联删除关联的标准答案
        # 软删除所有关联的标准答案
        db.query(models.StdAnswer).filter(
            models.StdAnswer.std_question_id.in_(question_ids),
            models.StdAnswer.is_valid == True
        ).update({"is_valid": False}, synchronize_session=False)
    else:  # 恢复操作 - 级联恢复关联的标准答案
        # 恢复所有关联的标准答案
        db.query(models.StdAnswer).filter(
            models.StdAnswer.std_question_id.in_(question_ids),
            models.StdAnswer.is_valid == False
        ).update({"is_valid": True}, synchronize_session=False)
    
    # 更新标准问题状态
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
        original_dataset_id=question.original_dataset_id,
        current_dataset_id=question.current_dataset_id,
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
    update_data = question.dict(exclude_unset=True, exclude={'tags'})
    for field, value in update_data.items():
        setattr(db_question, field, value)
    
    # 处理标签更新
    if question.tags is not None:
        # 清除现有标签关联
        db_question.tags.clear()
        
        # 添加新标签
        for tag_label in question.tags:
            # 查找或创建标签
            tag = db.query(models.Tag).filter(models.Tag.label == tag_label).first()
            if not tag:
                tag = models.Tag(label=tag_label)
                db.add(tag)
                db.flush()  # 确保标签有ID
            
            # 关联标签到问题
            db_question.tags.append(tag)
    
    db.commit()
    db.refresh(db_question)
    return db_question
