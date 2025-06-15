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
from ..models.std_answer import StdAnswer, StdAnswerScoringPoint
from ..models.tag import Tag
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
    """完成数据集版本工作，创建新版本"""
    work = db.query(DatasetVersionWork).filter(
        and_(
            DatasetVersionWork.id == work_id,
            DatasetVersionWork.created_by == user_id,
            DatasetVersionWork.work_status == WorkStatus.IN_PROGRESS
        )
    ).first()
    
    if not work:
        return None
    
    try:
        # 应用所有修改到实际数据集，创建新版本
        _apply_version_changes(db, work)
        
        work.work_status = WorkStatus.COMPLETED
        work.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(work)
        return work
    except Exception as e:
        db.rollback()
        raise e


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


# ============ Version Application Functions ============

def _apply_version_changes(db: Session, work: DatasetVersionWork):
    """应用版本工作中的所有变更到实际数据库"""
    from ..models.dataset import Dataset
    from ..models.std_question import StdQuestion
    from ..models.std_answer import StdAnswer
    from ..models.tag import Tag
    from ..crud.crud_std_question import get_std_question_tags
    
    # 1. 创建新的数据集版本
    new_dataset_version = Dataset(
        id=work.dataset_id,
        version=work.target_version,
        name=f"Dataset {work.dataset_id} v{work.target_version}",
        description=work.work_description or f"Version {work.target_version}",
        created_by=work.created_by,
        is_public=False,
        is_valid=True
    )
    db.add(new_dataset_version)
    
    # 2. 处理所有版本问题
    version_questions = db.query(VersionStdQuestion).filter(
        VersionStdQuestion.version_work_id == work.id
    ).all()
    
    for v_question in version_questions:
        if v_question.is_deleted:
            # 跳过已删除的问题
            continue
            
        if v_question.is_new or v_question.is_modified:
            # 创建新的标准问题
            new_question = _create_new_std_question(db, v_question, work)
            
            # 处理该问题的答案
            _process_question_answers(db, v_question, new_question, work)
            
        else:
            # 未修改的问题，只更新 current_version_id
            if v_question.original_question_id:
                original_question = db.query(StdQuestion).filter(
                    StdQuestion.id == v_question.original_question_id
                ).first()
                if original_question:
                    original_question.current_version_id = work.target_version
    
    db.flush()  # 确保所有更改都被写入


def _create_new_std_question(db: Session, v_question: VersionStdQuestion, work: DatasetVersionWork) -> StdQuestion:
    """创建新的标准问题"""
    from ..models.std_question import StdQuestion
    
    # 确定问题内容和类型
    if v_question.is_new:
        body = v_question.modified_body
        question_type = v_question.modified_question_type or 'text'
        original_version_id = work.target_version
        previous_version_id = None
    else:  # is_modified
        original_question = db.query(StdQuestion).filter(
            StdQuestion.id == v_question.original_question_id
        ).first()
        
        body = v_question.modified_body or original_question.body
        question_type = v_question.modified_question_type or original_question.question_type
        original_version_id = original_question.original_version_id
        previous_version_id = v_question.original_question_id
    
    # 创建新问题
    new_question = StdQuestion(
        dataset_id=work.dataset_id,
        body=body,
        question_type=question_type,
        is_valid=True,
        created_by=work.created_by,
        version=1,  # 新问题的版本总是从1开始
        previous_version_id=previous_version_id,
        original_version_id=original_version_id,
        current_version_id=work.target_version
    )
    
    db.add(new_question)
    db.flush()  # 获取新问题的ID
    
    # 处理标签
    _process_question_tags(db, v_question, new_question)
    
    return new_question


def _process_question_answers(db: Session, v_question: VersionStdQuestion, new_question: StdQuestion, work: DatasetVersionWork):
    """处理问题的答案"""
    from ..models.std_answer import StdAnswer
    
    # 获取该版本问题的所有答案
    version_answers = db.query(VersionStdAnswer).filter(
        VersionStdAnswer.version_question_id == v_question.id
    ).all()
    
    for v_answer in version_answers:
        if v_answer.is_deleted:
            continue
            
        if v_answer.is_new or v_answer.is_modified:
            # 创建新的标准答案
            new_answer = _create_new_std_answer(db, v_answer, new_question, work)
            
            # 处理得分点
            _process_answer_scoring_points(db, v_answer, new_answer, work)
        else:
            # 未修改的答案，需要复制到新问题下
            if v_answer.original_answer_id:
                original_answer = db.query(StdAnswer).filter(
                    StdAnswer.id == v_answer.original_answer_id
                ).first()
                if original_answer:
                    # 创建答案副本
                    new_answer = StdAnswer(
                        std_question_id=new_question.id,
                        answer=original_answer.answer,
                        is_valid=original_answer.is_valid,
                        answered_by=original_answer.answered_by,
                        version=1,
                        previous_version_id=v_answer.original_answer_id
                    )
                    db.add(new_answer)
                    db.flush()
                    
                    # 复制得分点
                    _copy_scoring_points(db, original_answer, new_answer)


def _create_new_std_answer(db: Session, v_answer: VersionStdAnswer, new_question: StdQuestion, work: DatasetVersionWork) -> StdAnswer:
    """创建新的标准答案"""
    from ..models.std_answer import StdAnswer
    
    if v_answer.is_new:
        answer_text = v_answer.modified_answer
        answered_by = v_answer.modified_answered_by or work.created_by
        previous_version_id = None
    else:  # is_modified
        original_answer = db.query(StdAnswer).filter(
            StdAnswer.id == v_answer.original_answer_id
        ).first()
        
        answer_text = v_answer.modified_answer or original_answer.answer
        answered_by = v_answer.modified_answered_by or original_answer.answered_by
        previous_version_id = v_answer.original_answer_id
    
    new_answer = StdAnswer(
        std_question_id=new_question.id,
        answer=answer_text,
        is_valid=True,
        answered_by=answered_by,
        version=1,
        previous_version_id=previous_version_id
    )
    
    db.add(new_answer)
    db.flush()
    return new_answer


def _process_answer_scoring_points(db: Session, v_answer: VersionStdAnswer, new_answer: StdAnswer, work: DatasetVersionWork):
    """处理答案的得分点"""
    from ..models.std_answer import StdAnswerScoringPoint
    
    # 获取该版本答案的所有得分点
    version_points = db.query(VersionScoringPoint).filter(
        VersionScoringPoint.version_answer_id == v_answer.id
    ).all()
    
    for v_point in version_points:
        if v_point.is_deleted:
            continue
            
        if v_point.is_new or v_point.is_modified:
            # 创建新的得分点
            if v_point.is_new:
                answer_text = v_point.modified_answer
                point_order = v_point.modified_point_order or 0
                answered_by = v_point.modified_answered_by or work.created_by
                previous_version_id = None
            else:  # is_modified
                original_point = db.query(StdAnswerScoringPoint).filter(
                    StdAnswerScoringPoint.id == v_point.original_point_id
                ).first()
                
                answer_text = v_point.modified_answer or original_point.answer
                point_order = v_point.modified_point_order if v_point.modified_point_order is not None else original_point.point_order
                answered_by = v_point.modified_answered_by or original_point.answered_by
                previous_version_id = v_point.original_point_id
            
            new_point = StdAnswerScoringPoint(
                std_answer_id=new_answer.id,
                answer=answer_text,
                point_order=point_order,
                is_valid=True,
                answered_by=answered_by,
                version=1,
                previous_version_id=previous_version_id
            )
            db.add(new_point)
        else:
            # 未修改的得分点，复制到新答案下
            if v_point.original_point_id:
                original_point = db.query(StdAnswerScoringPoint).filter(
                    StdAnswerScoringPoint.id == v_point.original_point_id
                ).first()
                if original_point:
                    new_point = StdAnswerScoringPoint(
                        std_answer_id=new_answer.id,
                        answer=original_point.answer,
                        point_order=original_point.point_order,
                        is_valid=original_point.is_valid,
                        answered_by=original_point.answered_by,
                        version=1,
                        previous_version_id=v_point.original_point_id
                    )
                    db.add(new_point)


def _copy_scoring_points(db: Session, original_answer: StdAnswer, new_answer: StdAnswer):
    """复制得分点到新答案"""
    from ..models.std_answer import StdAnswerScoringPoint
    
    original_points = db.query(StdAnswerScoringPoint).filter(
        StdAnswerScoringPoint.std_answer_id == original_answer.id,
        StdAnswerScoringPoint.is_valid == True
    ).all()
    
    for original_point in original_points:
        new_point = StdAnswerScoringPoint(
            std_answer_id=new_answer.id,
            answer=original_point.answer,
            point_order=original_point.point_order,
            is_valid=True,
            answered_by=original_point.answered_by,
            version=1,
            previous_version_id=original_point.id
        )
        db.add(new_point)


def _process_question_tags(db: Session, v_question: VersionStdQuestion, new_question: StdQuestion):
    """处理问题的标签"""
    from ..models.tag import Tag
    from ..crud.crud_relationship_records import create_question_tag_record
    
    # 获取该版本问题的所有标签
    version_tags = db.query(VersionTag).filter(
        VersionTag.version_question_id == v_question.id
    ).all()
    
    for v_tag in version_tags:
        if v_tag.is_deleted:
            continue
            
        # 查找或创建标签
        tag = db.query(Tag).filter(Tag.tag_label == v_tag.tag_label).first()
        if not tag:
            tag = Tag(tag_label=v_tag.tag_label)
            db.add(tag)
            db.flush()
        
        # 创建问题-标签关联
        create_question_tag_record(db, new_question.id, tag.id)


def load_dataset_to_version_work(db: Session, work_id: int, dataset_id: int, version: int) -> bool:
    """将现有数据集版本的数据加载到版本工作中"""
    # 获取版本工作
    work = db.query(DatasetVersionWork).filter(DatasetVersionWork.id == work_id).first()
    if not work:
        raise ValueError("Version work not found")
    
    # 获取指定版本的所有问题
    questions = db.query(StdQuestion).filter(
        StdQuestion.dataset_id == dataset_id,
        StdQuestion.current_version_id == version,
        StdQuestion.is_valid == True
    ).all()
    
    for question in questions:
        # 创建版本问题记录（标记为未修改）
        version_question = VersionStdQuestion(
            version_work_id=work_id,
            original_question_id=question.id,
            is_modified=False,
            is_new=False,
            is_deleted=False
        )
        db.add(version_question)
        db.flush()  # 获取ID
        
        # 加载问题的答案
        for answer in question.std_answers:
            if answer.is_valid:
                version_answer = VersionStdAnswer(
                    version_work_id=work_id,
                    version_question_id=version_question.id,
                    original_answer_id=answer.id,
                    is_modified=False,
                    is_deleted=False,
                    is_new=False
                )
                db.add(version_answer)
                db.flush()
                
                # 加载答案的得分点
                from ..models.std_answer import StdAnswerScoringPoint
                for point in db.query(StdAnswerScoringPoint).filter(
                    StdAnswerScoringPoint.std_answer_id == answer.id,
                    StdAnswerScoringPoint.is_valid == True
                ).all():
                    version_point = VersionScoringPoint(
                        version_work_id=work_id,
                        version_answer_id=version_answer.id,
                        original_point_id=point.id,
                        is_modified=False,
                        is_deleted=False,
                        is_new=False
                    )
                    db.add(version_point)
        
        # 加载问题的标签
        from ..crud.crud_std_question import get_std_question_tags
        tags = get_std_question_tags(db, question.id)
        for tag in tags:
            version_tag = VersionTag(
                version_work_id=work_id,
                version_question_id=version_question.id,
                tag_label=tag.tag_label,
                is_deleted=False,
                is_new=False
            )
            db.add(version_tag)
    
    db.commit()
    return True
