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

def get_raw_questions_count(db: Session, include_deleted: bool = False, deleted_only: bool = False, created_by: Optional[int] = None) -> int:
    """获取原始问题总数"""
    query = db.query(models.RawQuestion)
    
    if created_by is not None:
        query = query.filter(models.RawQuestion.created_by == created_by)
    
    if deleted_only:
        query = query.filter(models.RawQuestion.is_deleted == True)
    elif not include_deleted:
        query = query.filter(models.RawQuestion.is_deleted == False)
    
    return query.count()

def get_raw_questions_paginated(db: Session, skip: int = 0, limit: int = 10, include_deleted: bool = False, deleted_only: bool = False, created_by: int = None):
    """获取分页的原始问题数据和元数据"""
    # 获取数据
    query = db.query(models.RawQuestion).options(
        selectinload(models.RawQuestion.raw_answers.and_(models.RawAnswer.is_deleted == False)),
        selectinload(models.RawQuestion.expert_answers.and_(models.ExpertAnswer.is_deleted == False)),
        selectinload(models.RawQuestion.tags)
    )
    
    if created_by is not None:
        query = query.filter(models.RawQuestion.created_by == created_by)
    
    if deleted_only:
        # 只显示已删除的
        query = query.filter(models.RawQuestion.is_deleted == True)
    elif not include_deleted:
        # 只显示未删除的
        query = query.filter(models.RawQuestion.is_deleted == False)
    # 如果include_deleted=True且deleted_only=False，则显示全部
    
    questions = query.order_by(models.RawQuestion.id.asc()).offset(skip).limit(limit).all()
    
    # 获取总数
    total = get_raw_questions_count(db, include_deleted, deleted_only, created_by)
    
    return {
        "data": questions,
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit,
        "total_pages": (total + limit - 1) // limit,
        "has_next": skip + limit < total,
        "has_prev": skip > 0    }

def set_raw_question_deleted_status(db: Session, question_id: int, deleted_status: bool) -> Optional[models.RawQuestion]:
    db_question = db.query(models.RawQuestion).filter(models.RawQuestion.id == question_id).first()
    if db_question:
        db_question.is_deleted = deleted_status
        
        # 只在删除时级联删除相关回答，恢复时不自动恢复回答
        if deleted_status:  # 删除操作 - 级联删除相关回答
            # 软删除所有相关的原始回答和专家回答
            db.query(RawAnswer).filter(
                RawAnswer.question_id == question_id,
                RawAnswer.is_deleted == False
            ).update({"is_deleted": True}, synchronize_session=False)
            
            db.query(ExpertAnswer).filter(
                ExpertAnswer.question_id == question_id,
                ExpertAnswer.is_deleted == False
            ).update({"is_deleted": True}, synchronize_session=False)
        # 恢复问题时不自动恢复回答，回答需要单独恢复
        
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
    
    # 只在删除时级联删除相关回答，恢复时不自动恢复回答
    if deleted_status:  # 删除操作 - 级联删除相关回答
        # 软删除所有相关的原始回答和专家回答
        db.query(RawAnswer).filter(
            RawAnswer.question_id.in_(question_ids),
            RawAnswer.is_deleted == False
        ).update({"is_deleted": True}, synchronize_session=False)
        
        db.query(ExpertAnswer).filter(
            ExpertAnswer.question_id.in_(question_ids),
            ExpertAnswer.is_deleted == False
        ).update({"is_deleted": True}, synchronize_session=False)
    # 恢复问题时不自动恢复回答，回答需要单独恢复
    
    # 更新问题状态
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
        db.query(StdQuestion).filter(StdQuestion.id == question_id).delete(synchronize_session=False)
        
        # 4. 最后删除问题本身
        num_deleted = db.query(models.RawQuestion).filter(models.RawQuestion.id == question_id).delete(synchronize_session=False)
        
        db.commit()
        return num_deleted > 0
    except Exception as e:
        db.rollback()
        print(f"Error in force_delete_raw_question: {e}")  # 添加日志输出以便调试
        return False

def create_raw_question(question: schemas.RawQuestionCreate, created_by: int = None) -> models.RawQuestion:
    """创建新的原始问题"""
    # 处理空字符串URL - 转换为None以避免唯一约束冲突
    url_value = question.url if question.url and question.url.strip() else None
    
    db_question = models.RawQuestion(
        title=question.title,
        url=url_value,  
        body=question.body,
        votes=question.votes,
        views=question.views,
        author=question.author,
        tags_json=question.tags_json,
        issued_at=question.issued_at,
        created_by=created_by,
        is_deleted=False  # 默认不删除
    )
    return db_question

def create_raw_question_with_answers(db: Session, question_data: schemas.RawQuestionCreate, answers_data: List[dict], created_by: int = None) -> dict:
    """事务性地创建问题和相关回答"""
    try:
        # 1. 创建问题
        question = create_raw_question(question_data, created_by)
        db.add(question)
        db.flush()  # 刷新以获取问题ID
        
        # 2. 创建所有回答
        created_answers = []
        for answer_data in answers_data:
            # 为每个回答添加 question_id 和 created_by
            answer_create_data = {
                'question_id': question.id,
                'answer': answer_data.get('answer', ''),
                'answered_by': answer_data.get('answered_by'),
                'upvotes': answer_data.get('upvotes', '0'),
                'answered_at': answer_data.get('answered_at'),
                'created_by': created_by,
                'is_deleted': False
            }
            
            # 创建 RawAnswerCreate 对象
            from ..schemas.raw_answer import RawAnswerCreate
            answer_schema = RawAnswerCreate(**answer_create_data)
            
            # 创建回答
            answer_dict = answer_schema.dict()
            if "is_deleted" not in answer_dict:
                answer_dict["is_deleted"] = False
            
            db_answer = models.RawAnswer(**answer_dict)
            db.add(db_answer)
            db.flush()  # 刷新以获取ID，但不提交
            created_answers.append(db_answer)
        
        # 3. 提交整个事务
        db.commit()
        
        # 4. 重新加载数据以包含关系
        db.refresh(question)
        for answer in created_answers:
            db.refresh(answer)
        
        return {
            'question': question,
            'answers': created_answers,
            'success': True
        }
        
    except Exception as e:
        # 发生错误时回滚
        db.rollback()
        raise e