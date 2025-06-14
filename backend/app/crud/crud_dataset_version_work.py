"""
CRUD operations for Dataset Version Work
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.version_tables import (
    DatasetVersionWork, VersionStdQuestion, VersionStdAnswer, 
    VersionScoringPoint, VersionTag
)
from ..models.dataset import Dataset
from ..models.std_question import StdQuestion
from ..models.user import User
from ..schemas.dataset_version_work import (
    DatasetVersionWorkCreate, DatasetVersionWorkUpdate,
    VersionStdQuestionCreate, VersionStdQuestionUpdate,
    VersionStdAnswerCreate, VersionStdAnswerUpdate,
    VersionScoringPointCreate, VersionScoringPointUpdate,
    VersionTagCreate, WorkStatus
)


# ============ Dataset Version Work CRUD ============

def create_dataset_version_work(
    db: Session, 
    work_data: DatasetVersionWorkCreate, 
    user_id: int
) -> DatasetVersionWork:
    """创建数据集版本工作"""
    # 验证数据集存在
    dataset = db.query(Dataset).filter(Dataset.id == work_data.dataset_id).first()
    if not dataset:
        raise ValueError(f"Dataset {work_data.dataset_id} not found")
    
    # 创建版本工作记录
    version_work = DatasetVersionWork(
        dataset_id=work_data.dataset_id,
        current_version=work_data.current_version,
        target_version=work_data.target_version,
        work_description=work_data.work_description,
        notes=work_data.notes,
        created_by=user_id,
        work_status=WorkStatus.IN_PROGRESS
    )
    
    db.add(version_work)
    db.commit()
    db.refresh(version_work)
    return version_work


def get_dataset_version_work(db: Session, work_id: int) -> Optional[DatasetVersionWork]:
    """获取数据集版本工作详情"""
    return db.query(DatasetVersionWork).options(
        joinedload(DatasetVersionWork.version_questions).joinedload(VersionStdQuestion.version_tags),
        joinedload(DatasetVersionWork.version_answers),
        joinedload(DatasetVersionWork.version_scoring_points),
        joinedload(DatasetVersionWork.version_tags)
    ).filter(DatasetVersionWork.id == work_id).first()


def get_user_version_works(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 20,
    status: Optional[WorkStatus] = None,
    dataset_id: Optional[int] = None
) -> List[DatasetVersionWork]:
    """获取用户的版本工作列表"""
    query = db.query(DatasetVersionWork).filter(DatasetVersionWork.created_by == user_id)
    
    if status:
        query = query.filter(DatasetVersionWork.work_status == status)
        
    if dataset_id:
        query = query.filter(DatasetVersionWork.dataset_id == dataset_id)
    
    return query.order_by(desc(DatasetVersionWork.created_at)).offset(skip).limit(limit).all()


def get_dataset_version_works(
    db: Session, 
    dataset_id: int, 
    skip: int = 0, 
    limit: int = 20,
    status: Optional[WorkStatus] = None
) -> List[DatasetVersionWork]:
    """获取数据集的版本工作列表"""
    query = db.query(DatasetVersionWork).filter(DatasetVersionWork.dataset_id == dataset_id)
    
    if status:
        query = query.filter(DatasetVersionWork.work_status == status)
    
    return query.order_by(desc(DatasetVersionWork.created_at)).offset(skip).limit(limit).all()


def update_dataset_version_work(
    db: Session, 
    work_id: int, 
    work_update: DatasetVersionWorkUpdate,
    user_id: Optional[int] = None
) -> Optional[DatasetVersionWork]:
    """更新数据集版本工作"""
    query = db.query(DatasetVersionWork).filter(DatasetVersionWork.id == work_id)
    
    # 如果指定了用户ID，则只允许创建者更新
    if user_id:
        query = query.filter(DatasetVersionWork.created_by == user_id)
    
    work = query.first()
    if not work:
        return None
    
    update_data = work_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(work, field, value)
    
    db.commit()
    db.refresh(work)
    return work


def complete_dataset_version_work(
    db: Session, 
    work_id: int, 
    user_id: int
) -> Optional[DatasetVersionWork]:
    """完成数据集版本工作"""
    work = db.query(DatasetVersionWork).filter(
        and_(
            DatasetVersionWork.id == work_id,
            DatasetVersionWork.created_by == user_id,
            DatasetVersionWork.work_status == WorkStatus.IN_PROGRESS
        )
    ).first()
    
    if not work:
        return None
    
    # 应用所有修改到实际数据集
    # TODO: 实现具体的版本发布逻辑
    
    work.work_status = WorkStatus.COMPLETED
    work.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(work)
    return work


def cancel_dataset_version_work(
    db: Session, 
    work_id: int, 
    user_id: int
) -> Optional[DatasetVersionWork]:
    """取消数据集版本工作"""
    work = db.query(DatasetVersionWork).filter(
        and_(
            DatasetVersionWork.id == work_id,
            DatasetVersionWork.created_by == user_id,
            DatasetVersionWork.work_status == WorkStatus.IN_PROGRESS
        )
    ).first()
    
    if not work:
        return None
    
    work.work_status = WorkStatus.CANCELLED
    work.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(work)
    return work


def delete_dataset_version_work(
    db: Session, 
    work_id: int, 
    user_id: int
) -> bool:
    """删除数据集版本工作（仅允许删除未完成的工作）"""
    work = db.query(DatasetVersionWork).filter(
        and_(
            DatasetVersionWork.id == work_id,
            DatasetVersionWork.created_by == user_id,
            DatasetVersionWork.work_status.in_([WorkStatus.IN_PROGRESS, WorkStatus.CANCELLED])
        )
    ).first()
    
    if not work:
        return False
    
    db.delete(work)
    db.commit()
    return True


# ============ Version Question CRUD ============

def create_version_question(
    db: Session, 
    work_id: int,
    question_data: VersionStdQuestionCreate
) -> VersionStdQuestion:
    """创建版本问题"""
    version_question = VersionStdQuestion(
        version_work_id=work_id,
        original_question_id=question_data.original_question_id,
        is_modified=question_data.is_modified,
        is_new=question_data.is_new,
        is_deleted=question_data.is_deleted,
        modified_body=question_data.modified_body,
        modified_question_type=question_data.modified_question_type
    )
    
    db.add(version_question)
    db.commit()
    db.refresh(version_question)
    return version_question


def get_version_questions(
    db: Session, 
    work_id: int
) -> List[VersionStdQuestion]:
    """获取版本工作的所有问题"""
    return db.query(VersionStdQuestion).options(
        joinedload(VersionStdQuestion.version_tags),
        joinedload(VersionStdQuestion.version_answers),
        joinedload(VersionStdQuestion.original_question)
    ).filter(VersionStdQuestion.version_work_id == work_id).all()


def update_version_question(
    db: Session, 
    question_id: int, 
    question_update: VersionStdQuestionUpdate
) -> Optional[VersionStdQuestion]:
    """更新版本问题"""
    question = db.query(VersionStdQuestion).filter(VersionStdQuestion.id == question_id).first()
    if not question:
        return None
    
    update_data = question_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)
    
    db.commit()
    db.refresh(question)
    return question


def delete_version_question(db: Session, question_id: int) -> bool:
    """删除版本问题"""
    question = db.query(VersionStdQuestion).filter(VersionStdQuestion.id == question_id).first()
    if not question:
        return False
    
    db.delete(question)
    db.commit()
    return True


# ============ Version Answer CRUD ============

def create_version_answer(
    db: Session, 
    work_id: int,
    answer_data: VersionStdAnswerCreate
) -> VersionStdAnswer:
    """创建版本答案"""
    version_answer = VersionStdAnswer(
        version_work_id=work_id,
        version_question_id=answer_data.version_question_id,
        original_answer_id=answer_data.original_answer_id,
        is_modified=answer_data.is_modified,
        is_deleted=answer_data.is_deleted,
        is_new=answer_data.is_new,
        modified_answer=answer_data.modified_answer,
        modified_answered_by=answer_data.modified_answered_by
    )
    
    db.add(version_answer)
    db.commit()
    db.refresh(version_answer)
    return version_answer


def update_version_answer(
    db: Session, 
    answer_id: int, 
    answer_update: VersionStdAnswerUpdate
) -> Optional[VersionStdAnswer]:
    """更新版本答案"""
    answer = db.query(VersionStdAnswer).filter(VersionStdAnswer.id == answer_id).first()
    if not answer:
        return None
    
    update_data = answer_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(answer, field, value)
    
    db.commit()
    db.refresh(answer)
    return answer


# ============ Version Tag CRUD ============

def create_version_tag(
    db: Session, 
    work_id: int,
    tag_data: VersionTagCreate
) -> VersionTag:
    """创建版本标签"""
    version_tag = VersionTag(
        version_work_id=work_id,
        version_question_id=tag_data.version_question_id,
        tag_label=tag_data.tag_label,
        is_deleted=tag_data.is_deleted,
        is_new=tag_data.is_new
    )
    
    db.add(version_tag)
    db.commit()
    db.refresh(version_tag)
    return version_tag


def get_version_work_statistics(db: Session, work_id: int) -> Dict[str, int]:
    """获取版本工作的统计信息"""
    questions = db.query(VersionStdQuestion).filter(VersionStdQuestion.version_work_id == work_id).all()
    
    return {
        "total_questions": len(questions),
        "modified_questions": len([q for q in questions if q.is_modified]),
        "new_questions": len([q for q in questions if q.is_new]),
        "deleted_questions": len([q for q in questions if q.is_deleted])
    }
