from sqlalchemy.orm import Session, selectinload
from app import models, schemas
from typing import List, Optional
from datetime import datetime

def get_std_answer(db: Session, answer_id: int, include_deleted: bool = False) -> Optional[models.StdAnswer]:
    query = db.query(models.StdAnswer).options(
        selectinload(models.StdAnswer.std_question),
        selectinload(models.StdAnswer.scoring_points),  # 加载所有得分点，包括已删除的
        selectinload(models.StdAnswer.answered_by_user),
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

def get_std_answers_paginated(
    db: Session, 
    skip: int = 0, 
    limit: int = 10, 
    include_deleted: bool = False, 
    deleted_only: bool = False,
    dataset_id: Optional[int] = None,
    search_query: Optional[str] = None,
    std_question_filter: Optional[str] = None,
    scoring_point_filter: Optional[str] = None,
    scoring_points_filter: Optional[str] = None
):
    """获取分页的标准答案数据和元数据，支持搜索和筛选"""
    from ..schemas.common import PaginatedResponse
    from sqlalchemy import and_, or_, exists      # 构建基础查询
    query = db.query(models.StdAnswer).options(
        selectinload(models.StdAnswer.std_question),
        selectinload(models.StdAnswer.scoring_points),  # 加载所有得分点，包括已删除的
        selectinload(models.StdAnswer.answered_by_user),
    )
    
    # 应用删除状态过滤    
    if deleted_only:
        query = query.filter(models.StdAnswer.is_valid == False)
    elif not include_deleted:
        query = query.filter(models.StdAnswer.is_valid == True)
    
    # 应用数据集过滤（通过问题关联的数据集ID）
    if dataset_id is not None:
        query = query.join(models.StdQuestion).filter(
            models.StdQuestion.dataset_id == dataset_id  
        )
    
    # 应用搜索查询（搜索答案内容）
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(models.StdAnswer.answer.ilike(search_term))
    
    # 应用标准问题过滤
    if std_question_filter:
        search_term = f"%{std_question_filter}%"
        if not any(['join' in str(query).lower(), 'stdquestion' in str(query).lower()]):
            query = query.join(models.StdQuestion)
        query = query.filter(models.StdQuestion.body.ilike(search_term))
    
    # 应用得分点内容搜索过滤
    if scoring_point_filter:
        search_term = f"%{scoring_point_filter}%"
        query = query.join(models.StdAnswerScoringPoint).filter(
            and_(
                models.StdAnswerScoringPoint.answer.ilike(search_term),
                models.StdAnswerScoringPoint.is_valid == True
            )
        )
    
    # 应用得分点筛选（有得分点或无得分点）
    if scoring_points_filter:
        if scoring_points_filter == "has_scoring_points":
            # 筛选有得分点的答案
            query = query.filter(
                exists().where(
                    and_(
                        models.StdAnswerScoringPoint.std_answer_id == models.StdAnswer.id,
                        models.StdAnswerScoringPoint.is_valid == True
                    )
                )
            )
        elif scoring_points_filter == "no_scoring_points":
            # 筛选无得分点的答案
            query = query.filter(
                ~exists().where(
                    and_(
                        models.StdAnswerScoringPoint.std_answer_id == models.StdAnswer.id,
                        models.StdAnswerScoringPoint.is_valid == True
                    )
                )
            )
    
    # 去重（如果有联接的话）
    if std_question_filter or scoring_point_filter:
        query = query.distinct()
    
    # 获取总数
    total = query.count()
    
    # 获取分页数据
    answers = query.order_by(models.StdAnswer.id.asc()).offset(skip).limit(limit).all()    # 转换为字典格式以避免序列化问题
    answers_data = []
    for answer in answers:        # 获取得分点列表
        scoring_points_list = []
        scoring_points_data = []
        
        # 调试信息
        print(f"Answer {answer.id}: has {len(answer.scoring_points) if answer.scoring_points else 0} scoring points")
        
        if answer.scoring_points:
            for point in answer.scoring_points:
                # 暂时显示所有得分点，包括无效的，用于调试
                print(f"  Point {point.id}: {point.answer[:50]}... (valid: {point.is_valid})")
                scoring_points_list.append(point.answer)
                scoring_points_data.append({
                    "id": point.id,
                    "answer": point.answer,  
                    "std_answer_id": point.std_answer_id,
                    "point_order": point.point_order,
                    "is_valid": point.is_valid,
                    "previous_version_id": point.previous_version_id
                })
        
        answered_by = answer.answered_by_user.username if answer.answered_by_user else "unknown"

        answer_dict = {
            "id": answer.id,
            "std_question_id": answer.std_question_id,
            "answer": answer.answer,
            "answered_by": answered_by,
            "answered_at": answer.answered_at,
            "is_valid": answer.is_valid,
            "std_question": {
                "id": answer.std_question.id,
                "body": answer.std_question.body,
                "question_type": answer.std_question.question_type
            } if answer.std_question else None,
            "scoring_points_count": len(scoring_points_list),  # 新增：得分点数量
            "scoring_points": scoring_points_data
        }
        
        # 调试信息：打印每个答案的得分点情况
        print(f"Answer {answer.id}: has {len(scoring_points_data)} scoring points")
        for i, point in enumerate(scoring_points_data):
            print(f"  Point {point['id']}: {point['answer'][:50]}... (valid: {point['is_valid']})")
        
        answers_data.append(answer_dict)
    
    # 计算分页信息
    current_page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    return PaginatedResponse(
        data=answers_data,
        total=total,
        page=current_page,
        per_page=limit,
        total_pages=total_pages,
        has_next=skip + limit < total,
        has_prev=skip > 0
    )

def set_std_answer_deleted_status(db: Session, answer_id: int, deleted_status: bool) -> Optional[models.StdAnswer]:
    db_answer = db.query(models.StdAnswer).filter(models.StdAnswer.id == answer_id).first()
    if db_answer:
        question_id = db_answer.std_question_id
        db_answer.is_valid = not deleted_status  # StdAnswer uses is_valid instead of is_deleted
        
        # 如果是删除操作，检查是否需要级联删除关联的标准问题
        if deleted_status:
            # 检查该问题是否还有其他有效的标准答案
            remaining_answers = db.query(models.StdAnswer).filter(
                models.StdAnswer.std_question_id == question_id,
                models.StdAnswer.id != answer_id,
                models.StdAnswer.is_valid == True
            ).count()
            
            # 如果没有其他有效答案，同时删除标准问题
            if remaining_answers == 0:
                db.query(models.StdQuestion).filter(
                    models.StdQuestion.id == question_id,
                    models.StdQuestion.is_valid == True
                ).update({"is_valid": False}, synchronize_session=False)
        else:
            # 如果是恢复操作，同时恢复关联的标准问题
            db.query(models.StdQuestion).filter(
                models.StdQuestion.id == question_id,
                models.StdQuestion.is_valid == False
            ).update({"is_valid": True}, synchronize_session=False)
        
        db.commit()
        db.refresh(db_answer)
        return db_answer
    return None

def set_multiple_std_answers_deleted_status(db: Session, answer_ids: List[int], deleted_status: bool) -> int:
    # 获取所有要操作的答案及其关联的问题ID
    answers = db.query(models.StdAnswer).filter(
        models.StdAnswer.id.in_(answer_ids)
    ).all()
    
    if not answers:
        return 0
    
    # 收集所有涉及的问题ID
    question_ids = set(answer.std_question_id for answer in answers)
    
    # 更新答案的删除状态
    affected_rows = db.query(models.StdAnswer).filter(
        models.StdAnswer.id.in_(answer_ids)
    ).update({models.StdAnswer.is_valid: not deleted_status}, synchronize_session=False)
    
    # 处理级联删除/恢复逻辑
    for question_id in question_ids:
        if deleted_status:
            # 删除操作：检查该问题是否还有其他有效的标准答案
            remaining_answers = db.query(models.StdAnswer).filter(
                models.StdAnswer.std_question_id == question_id,
                models.StdAnswer.is_valid == True
            ).count()
            
            # 如果没有其他有效答案，同时删除标准问题
            if remaining_answers == 0:
                db.query(models.StdQuestion).filter(
                    models.StdQuestion.id == question_id,
                    models.StdQuestion.is_valid == True
                ).update({"is_valid": False}, synchronize_session=False)
        else:
            # 恢复操作：同时恢复关联的标准问题
            db.query(models.StdQuestion).filter(
                models.StdQuestion.id == question_id,
                models.StdQuestion.is_valid == False
            ).update({"is_valid": True}, synchronize_session=False)
    
    db.commit()
    return affected_rows

def force_delete_std_answer(db: Session, answer_id: int) -> bool:
    """永久删除标准答案"""
    try:
        # 获取标准答案及其关联的问题ID
        db_answer = db.query(models.StdAnswer).filter(models.StdAnswer.id == answer_id).first()
        if not db_answer:
            return False
        
        question_id = db_answer.std_question_id
          # 首先删除相关的评分点
        db.query(models.StdAnswerScoringPoint).filter(
            models.StdAnswerScoringPoint.std_answer_id == answer_id
        ).delete(synchronize_session=False)        
        
        # 删除标准答案和原始答案的关联记录
        db.query(models.StdAnswerRawAnswerRecord).filter(
            models.StdAnswerRawAnswerRecord.std_answer_id == answer_id
        ).delete(synchronize_session=False)
        
        # 删除标准答案和专家答案的关联记录  
        db.query(models.StdAnswerExpertAnswerRecord).filter(
            models.StdAnswerExpertAnswerRecord.std_answer_id == answer_id
        ).delete(synchronize_session=False)
        
        # 删除标准答案
        db.query(models.StdAnswer).filter(models.StdAnswer.id == answer_id).delete(synchronize_session=False)
        
        # 检查该问题是否还有其他标准答案
        remaining_answers = db.query(models.StdAnswer).filter(
            models.StdAnswer.std_question_id == question_id
        ).count()
        # 如果没有其他答案，强制删除关联的标准问题
        if remaining_answers == 0:
            # 获取标准问题对象以清理标签关系
            std_question = db.query(models.StdQuestion).filter(
                models.StdQuestion.id == question_id
            ).first()
            
            if std_question:
                # 清除标准问题的标签关联（多对多关系）
                std_question.tags.clear()
                db.flush()  # 确保标签关系被清理
            
            # 删除标准问题的相关关系记录
            db.query(models.StdQuestionRawQuestionRecord).filter(
                models.StdQuestionRawQuestionRecord.std_question_id == question_id
            ).delete(synchronize_session=False)
            
            # 删除标准问题
            db.query(models.StdQuestion).filter(
                models.StdQuestion.id == question_id
            ).delete(synchronize_session=False)
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error force deleting std answer {answer_id}: {e}")
        return False

def create_std_answer(db: Session, answer: schemas.StdAnswerCreate, dataset_version: Optional[int] = None) -> models.StdAnswer:
    """创建标准回答
    
    Args:
        db: 数据库会话
        answer: 答案创建数据
        dataset_version: 当前数据集版本，用于设置版本区间
    """
    # 如果没有提供数据集版本，从关联的问题获取
    if dataset_version is None and answer.std_question_id:
        question = db.query(models.StdQuestion).filter(
            models.StdQuestion.id == answer.std_question_id
        ).first()
        if question:
            # 从问题获取数据集信息
            dataset = db.query(models.Dataset).filter(
                models.Dataset.id == question.dataset_id
            ).first()
            if dataset:
                dataset_version = dataset.version
      # 确保版本区间字段有值
    original_version_id = answer.original_version_id or dataset_version
    current_version_id = answer.current_version_id or dataset_version
    
    if original_version_id is None or current_version_id is None:
        raise ValueError("original_version_id and current_version_id must be provided or dataset_version must be available")
    
    db_answer = models.StdAnswer(
        std_question_id=answer.std_question_id,
        answer=answer.answer,
        answered_by=answer.answered_by,  # 统一字段名为answered_by
        version=answer.version,
        previous_version_id=answer.previous_version_id,
        # 设置版本区间字段
        original_version_id=original_version_id,
        current_version_id=current_version_id,
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
            answer=scoring_point_data.answer,  # 统一字段名为answer
            point_order=scoring_point_data.point_order,
            answered_by=scoring_point_data.created_by
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
    
    # 只允许更新这些字段，排除版本管理和创建者相关字段
    allowed_fields = {'std_question_id', 'answer', 'is_valid'}
    update_data = answer.dict(exclude_unset=True, exclude={'scoring_points', 'referenced_raw_answer_ids', 'referenced_expert_answer_ids'})
      # 只更新允许的字段，明确排除用户相关和版本管理字段
    for field, value in update_data.items():
        if field in allowed_fields and value is not None:
            setattr(db_answer, field, value)
    
    # 更新原始回答的引用关系（可选功能）
    if hasattr(answer, 'referenced_raw_answer_ids') and answer.referenced_raw_answer_ids is not None:
        # 清除旧的引用
        db.query(models.RawAnswer).filter(
            models.RawAnswer.referenced_by_std_answer_id == answer_id
        ).update({models.RawAnswer.referenced_by_std_answer_id: None}, synchronize_session=False)
        
        # 设置新的引用
        if answer.referenced_raw_answer_ids:
            db.query(models.RawAnswer).filter(
                models.RawAnswer.id.in_(answer.referenced_raw_answer_ids)
            ).update({models.RawAnswer.referenced_by_std_answer_id: answer_id}, synchronize_session=False)
      # 更新专家回答的引用关系（可选功能）
    if hasattr(answer, 'referenced_expert_answer_ids') and answer.referenced_expert_answer_ids is not None:
        # 清除旧的引用
        db.query(models.ExpertAnswer).filter(
            models.ExpertAnswer.referenced_by_std_answer_id == answer_id
        ).update({models.ExpertAnswer.referenced_by_std_answer_id: None}, synchronize_session=False)
        
        # 设置新的引用
        if answer.referenced_expert_answer_ids:
            db.query(models.ExpertAnswer).filter(
                models.ExpertAnswer.id.in_(answer.referenced_expert_answer_ids)
            ).update({models.ExpertAnswer.referenced_by_std_answer_id: answer_id}, synchronize_session=False)
    
    # 如果提供了评分点，更新评分点（可选功能）
    if hasattr(answer, 'scoring_points') and answer.scoring_points is not None:
        # 删除现有评分点
        db.query(models.StdAnswerScoringPoint).filter(
            models.StdAnswerScoringPoint.std_answer_id == answer_id
        ).delete(synchronize_session=False)
        
        # 创建新的评分点
        for scoring_point_data in answer.scoring_points:
            db_scoring_point = models.StdAnswerScoringPoint(
                std_answer_id=answer_id,
                answer=scoring_point_data.answer,  # 使用正确的字段名
                point_order=scoring_point_data.point_order,
            )
            db.add(db_scoring_point)
    
    db.commit()
    db.refresh(db_answer)
    return db_answer

def get_std_answers_by_dataset_version(
    db: Session, 
    dataset_id: int, 
    dataset_version: int,
    include_deleted: bool = False
) -> List[models.StdAnswer]:
    """根据数据集版本获取标准答案
    
    Args:
        db: 数据库会话
        dataset_id: 数据集ID
        dataset_version: 数据集版本号
        include_deleted: 是否包含已删除的答案
    
    Returns:
        在该数据集版本中有效的标准答案列表
    """
    query = db.query(models.StdAnswer).options(
        selectinload(models.StdAnswer.std_question),
        selectinload(models.StdAnswer.scoring_points),
        selectinload(models.StdAnswer.answered_by_user),
    ).join(models.StdQuestion).filter(
        models.StdQuestion.dataset_id == dataset_id,
        # 答案在指定版本的有效区间内
        models.StdAnswer.original_version_id <= dataset_version,
        models.StdAnswer.current_version_id >= dataset_version
    )
    
    if not include_deleted:
        query = query.filter(models.StdAnswer.is_valid == True)
    
    return query.all()


def get_std_answer_by_id_and_version(
    db: Session, 
    answer_id: int, 
    dataset_version: int,
    include_deleted: bool = False
) -> Optional[models.StdAnswer]:
    """根据答案ID和数据集版本获取标准答案
    
    Args:
        db: 数据库会话
        answer_id: 答案ID
        dataset_version: 数据集版本号
        include_deleted: 是否包含已删除的答案
    
    Returns:
        在该版本中有效的标准答案，如果不存在则返回None
    """
    query = db.query(models.StdAnswer).options(
        selectinload(models.StdAnswer.std_question),
        selectinload(models.StdAnswer.scoring_points),
        selectinload(models.StdAnswer.answered_by_user),
    ).filter(
        models.StdAnswer.id == answer_id,
        # 答案在指定版本的有效区间内
        models.StdAnswer.original_version_id <= dataset_version,
        models.StdAnswer.current_version_id >= dataset_version
    )
    
    if not include_deleted:
        query = query.filter(models.StdAnswer.is_valid == True)
    
    return query.first()
