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
    db.flush()  # 获取版本工作ID
    
    # 创建目标版本的数据集（is_valid为False，等待最终确认）
    target_dataset = Dataset(
        id=work_data.dataset_id,
        name=dataset.name,
        description=dataset.description,
        version=work_data.target_version,
        created_by=dataset.created_by,
        is_public=dataset.is_public,
        is_valid=False  # 设置为无效，等待最终确认
    )
    db.add(target_dataset)
    
    db.commit()
    db.refresh(version_work)
    return version_work


def get_dataset_version_work(db: Session, work_id: int) -> Optional[DatasetVersionWork]:
    """获取数据集版本工作详情"""
    return db.query(DatasetVersionWork).options(
        joinedload(DatasetVersionWork.version_questions)
            .joinedload(VersionStdQuestion.original_question)
            .joinedload(StdQuestion.std_answers),
        joinedload(DatasetVersionWork.version_questions)
            .joinedload(VersionStdQuestion.version_tags),
        joinedload(DatasetVersionWork.version_answers)
            .joinedload(VersionStdAnswer.version_scoring_points),
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
        # 1. 获取目标版本的数据集（应该已经创建，但is_valid为False）
        target_dataset = db.query(Dataset).filter(
            Dataset.id == work.dataset_id,
            Dataset.version == work.target_version
        ).first()
        
        if not target_dataset:
            raise ValueError(f"Target dataset version {work.target_version} not found")
        
        # 2. 将目标数据集设置为有效（在应用更改之前）
        target_dataset.is_valid = True
        db.flush()  # 确保更改立即生效
        
        # 3. 应用版本工作表中的修改
        _apply_version_changes(db, work)
        
        # 4. 更新版本工作状态
        work.work_status = WorkStatus.COMPLETED
        work.completed_at = datetime.utcnow()
        
        db.commit()
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
        joinedload(VersionStdQuestion.original_question)
    ).filter(VersionStdQuestion.version_work_id == work_id).all()


def get_version_work_complete_data(db: Session, work_id: int) -> Dict[str, Any]:
    """获取版本工作的完整数据，包括版本答案"""
    # 获取版本工作信息
    work = db.query(DatasetVersionWork).filter(DatasetVersionWork.id == work_id).first()
    if not work:
        return {}
    
    # 获取版本问题
    version_questions = db.query(VersionStdQuestion).options(
        joinedload(VersionStdQuestion.version_tags),
        joinedload(VersionStdQuestion.original_question)
    ).filter(VersionStdQuestion.version_work_id == work_id).all()
    
    # 获取版本答案
    version_answers = db.query(VersionStdAnswer).options(
        joinedload(VersionStdAnswer.version_scoring_points),
        joinedload(VersionStdAnswer.original_answer)
    ).filter(VersionStdAnswer.version_work_id == work_id).all()
    
    # 为每个版本问题关联对应的版本答案
    for v_question in version_questions:
        v_question.version_answers = []
        
        if v_question.original_question_id:
            # 对于有原始问题ID的版本问题，查找对应的版本答案
            for v_answer in version_answers:
                if v_answer.original_answer_id:
                    # 检查这个版本答案是否属于当前问题
                    original_answer = v_answer.original_answer
                    if original_answer and original_answer.std_question_id == v_question.original_question_id:
                        v_question.version_answers.append(v_answer)
    
    return {
        "work": work,
        "version_questions": version_questions,
        "version_answers": version_answers
    }


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


def create_version_answer_with_scoring_points(
    db: Session, 
    work_id: int,
    answer_data: VersionStdAnswerCreate,
    scoring_points_data: Optional[List[Dict[str, Any]]] = None
) -> VersionStdAnswer:
    """创建版本答案并同时处理得分点"""
    # 创建版本答案
    version_answer = create_version_answer(db, work_id, answer_data)
    
    # 如果有得分点数据，创建版本得分点记录
    if scoring_points_data and answer_data.original_answer_id:
        from ..models.std_answer import StdAnswerScoringPoint
        
        # 获取原始答案的所有得分点
        original_points = db.query(StdAnswerScoringPoint).filter(
            StdAnswerScoringPoint.std_answer_id == answer_data.original_answer_id,
            StdAnswerScoringPoint.is_valid == True
        ).all()
        
        # 为每个原始得分点创建版本记录
        for original_point in original_points:
            # 查找对应的新得分点数据
            new_point_data = next((p for p in scoring_points_data if p.get('id') == original_point.id), None)
            
            if new_point_data:
                # 检查是否有修改
                is_modified = (original_point.answer != new_point_data.get('answer') or 
                              original_point.point_order != new_point_data.get('point_order'))
                
                if is_modified:
                    # 创建修改的版本得分点记录
                    version_point = VersionScoringPoint(
                        version_work_id=work_id,
                        version_answer_id=version_answer.id,
                        original_point_id=original_point.id,
                        is_modified=True,
                        is_deleted=False,
                        is_new=False,
                        modified_answer=new_point_data.get('answer'),
                        modified_point_order=new_point_data.get('point_order')
                    )
                    db.add(version_point)
            else:
                # 得分点被删除
                version_point = VersionScoringPoint(
                    version_work_id=work_id,
                    version_answer_id=version_answer.id,
                    original_point_id=original_point.id,
                    is_modified=False,
                    is_deleted=True,
                    is_new=False
                )
                db.add(version_point)
        
        # 处理新增的得分点
        for new_point_data in scoring_points_data:
            point_id = new_point_data.get('id')
            if not point_id or (isinstance(point_id, str) and point_id.startswith('new_')):
                # 新增的得分点
                version_point = VersionScoringPoint(
                    version_work_id=work_id,
                    version_answer_id=version_answer.id,
                    original_point_id=None,
                    is_modified=False,
                    is_deleted=False,
                    is_new=True,
                    modified_answer=new_point_data.get('answer'),
                    modified_point_order=new_point_data.get('point_order')
                )
                db.add(version_point)
        
        db.commit()
    
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
    
    # 1. 验证目标数据集版本存在且有效
    target_dataset = db.query(Dataset).filter(
        Dataset.id == work.dataset_id,
        Dataset.version == work.target_version,
        Dataset.is_valid == True
    ).first()
    
    if not target_dataset:
        raise ValueError(f"Target dataset version {work.target_version} not found or not valid")
    
    # 2. 获取当前版本的所有问题
    current_questions = db.query(StdQuestion).filter(
        StdQuestion.dataset_id == work.dataset_id,
        StdQuestion.current_version_id == work.current_version,
        StdQuestion.is_valid == True
    ).all()
    
    # 3. 获取版本工作表中的所有问题记录
    version_questions = db.query(VersionStdQuestion).filter(
        VersionStdQuestion.version_work_id == work.id
    ).all()
    
    # 4. 处理所有版本问题
    for v_question in version_questions:
        if v_question.is_deleted:
            # 删除的问题：保持原始问题的版本区间不变
            # 这样删除的问题在新版本中不会出现
            continue
            
        if v_question.is_new:
            # 新增的问题：由于目标版本数据集已经创建，可以直接添加到标准表中
            if v_question.original_question_id:
                new_question = db.query(StdQuestion).filter(
                    StdQuestion.id == v_question.original_question_id
                ).first()
                if new_question:
                    # 确保版本ID指向目标版本
                    new_question.current_version_id = work.target_version
        elif v_question.is_modified:
            # 修改的问题：创建新的问题
            new_question = _create_new_std_question(db, v_question, work)
            _process_question_answers(db, v_question, new_question, work)
        else:
            # 未修改的问题，扩展版本区间到包含新版本
            if v_question.original_question_id:
                original_question = db.query(StdQuestion).filter(
                    StdQuestion.id == v_question.original_question_id
                ).first()
                if original_question:
                    # 扩展原始问题的版本区间到包含新版本
                    original_question.current_version_id = work.target_version
    
    # 5. 处理未在版本工作表中记录的问题（完全未修改的问题）
    modified_question_ids = {vq.original_question_id for vq in version_questions if vq.original_question_id}
    unmodified_questions = [q for q in current_questions if q.id not in modified_question_ids]
    
    for question in unmodified_questions:
        # 扩展未修改问题的版本区间到包含新版本
        question.current_version_id = work.target_version
        
        # 同时扩展该问题下所有答案的版本区间
        for answer in question.std_answers:
            if answer.is_valid:
                answer.current_version_id = work.target_version


def _create_new_std_question(db: Session, v_question: VersionStdQuestion, work: DatasetVersionWork) -> StdQuestion:
    """创建新的标准问题"""
    from ..models.std_question import StdQuestion
    from ..models.relationship_records import StdQuestionRawQuestionRecord
    
    # 确定问题内容和类型
    if v_question.is_new:
        body = v_question.modified_body
        question_type = v_question.modified_question_type or 'text'
        # 新增问题的版本ID逻辑：original_version_id和current_version_id都指向目标版本
        # 这样新增的数据不会与原有版本产生关联
        original_version_id = work.target_version
        previous_version_id = None
    else:  # is_modified
        original_question = db.query(StdQuestion).filter(
            StdQuestion.id == v_question.original_question_id
        ).first()
        
        body = v_question.modified_body or original_question.body
        question_type = v_question.modified_question_type or original_question.question_type
        # 修改的问题：original_version_id指向的是即将创建的新版本的数据集
        # previous_version_id是这个新建的数据的前一个版本
        original_version_id = work.target_version
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
    
    # 处理原始问题关联
    raw_question_ids = getattr(v_question, 'raw_question_ids', None)
    if raw_question_ids:
        for raw_question_id in raw_question_ids:
            record = StdQuestionRawQuestionRecord(
                std_question_id=new_question.id,
                raw_question_id=raw_question_id,
                created_by=work.created_by
            )
            db.add(record)
    # 对于被修改的问题，如果没有raw_question_ids，则自动继承原问题的关联
    if v_question.is_modified and not raw_question_ids:
        from ..models.relationship_records import StdQuestionRawQuestionRecord
        original_records = db.query(StdQuestionRawQuestionRecord).filter(
            StdQuestionRawQuestionRecord.std_question_id == v_question.original_question_id
        ).all()
        for rec in original_records:
            record = StdQuestionRawQuestionRecord(
                std_question_id=new_question.id,
                raw_question_id=rec.raw_question_id,
                created_by=work.created_by
            )
            db.add(record)
    return new_question


def _process_question_answers(db: Session, v_question: VersionStdQuestion, new_question: StdQuestion, work: DatasetVersionWork):
    """处理问题的答案"""
    from ..models.std_answer import StdAnswer
    
    # 获取该版本问题的所有答案
    # 由于版本答案和版本问题现在是独立的，我们需要通过原始问题ID来找到相关的答案
    if v_question.original_question_id:
        # 获取原始问题的所有答案
        original_answers = db.query(StdAnswer).filter(
            StdAnswer.std_question_id == v_question.original_question_id,
            StdAnswer.is_valid == True
        ).all()
        
        # 对于每个原始答案，检查是否有对应的版本答案记录
        for original_answer in original_answers:
            version_answer = db.query(VersionStdAnswer).filter(
                VersionStdAnswer.original_answer_id == original_answer.id,
                VersionStdAnswer.version_work_id == work.id
            ).first()
            
            if version_answer and version_answer.is_deleted:
                # 答案被删除，不处理
                continue
            elif version_answer and (version_answer.is_new or version_answer.is_modified):
                # 创建新的标准答案
                new_answer = _create_new_std_answer(db, version_answer, new_question, work)
                # 处理得分点
                _process_answer_scoring_points(db, version_answer, new_answer, work)
            else:
                # 未修改的答案，复制到新问题下并扩展版本区间
                new_answer = StdAnswer(
                    std_question_id=new_question.id,
                    answer=original_answer.answer,
                    is_valid=original_answer.is_valid,
                    answered_by=original_answer.answered_by,
                    version=1,
                    previous_version_id=original_answer.id,
                    # 设置版本区间：继承原答案的起始版本，当前版本为目标版本
                    original_version_id=original_answer.original_version_id or original_answer.id,
                    current_version_id=work.target_version
                )
                db.add(new_answer)
                db.flush()
                
                # 复制得分点
                _copy_scoring_points(db, original_answer, new_answer)
    
    # 处理新增的答案（通过original_answer_id关联到当前问题）
    if v_question.is_new and v_question.original_question_id:
        # 对于新增的问题，查找属于该问题的新增答案
        # 通过original_answer_id指向的标准答案的std_question_id来判断
        new_answers = db.query(VersionStdAnswer).join(
            StdAnswer, VersionStdAnswer.original_answer_id == StdAnswer.id
        ).filter(
            VersionStdAnswer.version_work_id == work.id,
            VersionStdAnswer.is_new == True,
            VersionStdAnswer.is_deleted == False,
            StdAnswer.std_question_id == v_question.original_question_id
        ).all()
        
        for version_answer in new_answers:
            # 创建新的标准答案
            new_answer = _create_new_std_answer(db, version_answer, new_question, work)
            # 处理得分点
            _process_answer_scoring_points(db, version_answer, new_answer, work)


def _create_new_std_answer(db: Session, v_answer: VersionStdAnswer, new_question: StdQuestion, work: DatasetVersionWork) -> StdAnswer:
    """创建新的标准答案"""
    from ..models.std_answer import StdAnswer
    from ..models.relationship_records import StdAnswerRawAnswerRecord, StdAnswerExpertAnswerRecord
    
    if v_answer.is_new:
        answer_text = v_answer.modified_answer
        answered_by = v_answer.modified_answered_by or work.created_by
        previous_version_id = None
        # 新增答案的版本ID逻辑：original_version_id和current_version_id都指向目标版本
        # 这样新增的数据不会与原有版本产生关联
        original_version_id = work.target_version
    else:  # is_modified
        if not v_answer.original_answer_id:
            raise ValueError("Modified answer must have original_answer_id")
            
        original_answer = db.query(StdAnswer).filter(
            StdAnswer.id == v_answer.original_answer_id
        ).first()
        
        answer_text = v_answer.modified_answer or original_answer.answer
        answered_by = v_answer.modified_answered_by or original_answer.answered_by
        # 修改的答案：original_version_id指向的是即将创建的新版本的数据集
        # previous_version_id是这个新建的数据的前一个版本
        previous_version_id = v_answer.original_answer_id
        original_version_id = work.target_version
    
    new_answer = StdAnswer(
        std_question_id=new_question.id,
        answer=answer_text,
        is_valid=True,
        answered_by=answered_by,
        version=1,
        previous_version_id=previous_version_id,
        original_version_id=original_version_id,
        current_version_id=work.target_version
    )
    
    db.add(new_answer)
    db.flush()

    # 处理原始回答关联
    raw_answer_ids = getattr(v_answer, 'raw_answer_ids', None)
    if raw_answer_ids:
        for raw_answer_id in raw_answer_ids:
            record = StdAnswerRawAnswerRecord(
                std_answer_id=new_answer.id,
                raw_answer_id=raw_answer_id,
                created_by=work.created_by
            )
            db.add(record)
    # 对于被修改的答案，如果没有raw_answer_ids，则自动继承原答案的关联
    if v_answer.is_modified and not raw_answer_ids:
        original_records = db.query(StdAnswerRawAnswerRecord).filter(
            StdAnswerRawAnswerRecord.std_answer_id == v_answer.original_answer_id
        ).all()
        for rec in original_records:
            record = StdAnswerRawAnswerRecord(
                std_answer_id=new_answer.id,
                raw_answer_id=rec.raw_answer_id,
                created_by=work.created_by
            )
            db.add(record)

    # 处理专家回答关联
    expert_answer_ids = getattr(v_answer, 'expert_answer_ids', None)
    if expert_answer_ids:
        for expert_answer_id in expert_answer_ids:
            record = StdAnswerExpertAnswerRecord(
                std_answer_id=new_answer.id,
                expert_answer_id=expert_answer_id,
                created_by=work.created_by
            )
            db.add(record)
    # 对于被修改的答案，如果没有expert_answer_ids，则自动继承原答案的关联
    if v_answer.is_modified and not expert_answer_ids:
        original_records = db.query(StdAnswerExpertAnswerRecord).filter(
            StdAnswerExpertAnswerRecord.std_answer_id == v_answer.original_answer_id
        ).all()
        for rec in original_records:
            record = StdAnswerExpertAnswerRecord(
                std_answer_id=new_answer.id,
                expert_answer_id=rec.expert_answer_id,
                created_by=work.created_by
            )
            db.add(record)
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
        tag = db.query(Tag).filter(Tag.label == v_tag.tag_label).first()
        if not tag:
            tag = Tag(tag_label=v_tag.tag_label)
            db.add(tag)
            db.flush()
          # 创建问题-标签关联
        create_question_tag_record(db, new_question.id, tag.label)


def load_dataset_to_version_work(db: Session, work_id: int, dataset_id: int, version: int) -> bool:
    """将现有数据集版本的数据加载到版本工作中"""
    # 获取版本工作
    work = db.query(DatasetVersionWork).filter(DatasetVersionWork.id == work_id).first()
    if not work:
        raise ValueError("Version work not found")
    
    # 获取指定版本的所有问题 - 使用current_version_id字段查询
    questions = db.query(StdQuestion).filter(
        StdQuestion.dataset_id == dataset_id,
        StdQuestion.current_version_id == version,  # 使用current_version_id字段
        StdQuestion.is_valid == True
    ).all()
    
    for question in questions:
        # 创建版本问题记录（标记为未修改）
        version_question = VersionStdQuestion(
            version_work_id=work_id,
            original_question_id=question.id,
            is_modified=False,
            is_deleted=False,
            is_new=False
        )
        db.add(version_question)
        db.flush()  # 获取ID
        
        # 加载问题的答案
        for answer in question.std_answers:
            if answer.is_valid:
                version_answer = VersionStdAnswer(
                    version_work_id=work_id,
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
                tag_label=tag.label,
                is_deleted=False,
                is_new=False
            )
            db.add(version_tag)
    
    db.commit()
    return True


def _extend_question_answers_version(db: Session, v_question: VersionStdQuestion, original_question: StdQuestion, work: DatasetVersionWork):
    """扩展未修改问题下答案的版本区间"""
    from ..models.std_answer import StdAnswer, StdAnswerScoringPoint
    
    # 由于版本答案和版本问题现在是独立的，我们需要通过原始问题ID来找到相关的答案
    if v_question.original_question_id:
        # 获取原始问题的所有答案
        original_answers = db.query(StdAnswer).filter(
            StdAnswer.std_question_id == v_question.original_question_id,
            StdAnswer.is_valid == True
        ).all()
        
        # 对于每个原始答案，检查是否有对应的版本答案记录
        for original_answer in original_answers:
            version_answer = db.query(VersionStdAnswer).filter(
                VersionStdAnswer.original_answer_id == original_answer.id,
                VersionStdAnswer.version_work_id == work.id
            ).first()
            
            if not version_answer or not (version_answer.is_new or version_answer.is_modified):
                # 未修改的答案，扩展原始答案的版本区间
                original_answer.current_version_id = work.target_version


def _extend_answer_scoring_points_version(db: Session, v_answer: VersionStdAnswer, original_answer: StdAnswer, work: DatasetVersionWork):
    """得分点作为答案的属性，不需要单独的版本区间管理，此函数保留为空"""
    # 得分点跟随答案的版本，不需要单独处理
    pass


# ============ Complete Standard QA Pair Creation ============

def create_version_std_qa_pair(
    db: Session,
    work_id: int,
    qa_data: Dict[str, Any]
) -> Dict[str, Any]:
    """创建版本标准问答对"""
    # 1. 获取版本工作信息
    work = db.query(DatasetVersionWork).filter(DatasetVersionWork.id == work_id).first()
    if not work:
        raise ValueError("Version work not found")
    
    # 2. 验证目标版本数据集存在（应该已经创建，但is_valid为False）
    target_dataset = db.query(Dataset).filter(
        Dataset.id == work.dataset_id,
        Dataset.version == work.target_version
    ).first()
    
    if not target_dataset:
        raise ValueError(f"Target dataset version {work.target_version} not found")
    
    # 3. 同时创建标准问答对到标准表中（版本ID指向目标版本）
    # 创建标准问题
    std_question = StdQuestion(
        dataset_id=work.dataset_id,
        body=qa_data["question"],
        question_type=qa_data.get("question_type", "text"),
        is_valid=True,
        created_by=work.created_by,
        version=1,  # 新问题的版本总是从1开始
        previous_version_id=None,
        original_version_id=work.target_version,  # 指向目标版本
        current_version_id=work.target_version     # 指向目标版本
    )
    db.add(std_question)
    db.flush()  # 获取标准问题ID

    # 处理原始问题关联
    raw_question_ids = qa_data["raw_question_ids"]
    if raw_question_ids:
        from ..models.relationship_records import StdQuestionRawQuestionRecord
        for raw_question_id in raw_question_ids:
            record = StdQuestionRawQuestionRecord(
                std_question_id=std_question.id,
                raw_question_id=raw_question_id,
                created_by=work.created_by
            )
            db.add(record)
    
    # 创建标准答案
    std_answer = StdAnswer(
        std_question_id=std_question.id,
        answer=qa_data["answer"],
        is_valid=True,
        answered_by=work.created_by,
        version=1,
        previous_version_id=None,
        original_version_id=work.target_version,  # 指向目标版本
        current_version_id=work.target_version     # 指向目标版本
    )
    db.add(std_answer)
    db.flush()  # 获取标准答案ID

    # 4.1. 处理原始回答关联
    raw_answer_ids = qa_data["raw_answer_ids"]
    if raw_answer_ids:
        from ..models.relationship_records import StdAnswerRawAnswerRecord
        for raw_answer_id in raw_answer_ids:
            record = StdAnswerRawAnswerRecord(
                std_answer_id=std_answer.id,
                raw_answer_id=raw_answer_id,
                created_by=work.created_by
            )
            db.add(record)

    # 4.2. 处理专家回答关联
    expert_answer_ids = qa_data["expert_answer_ids"]
    if expert_answer_ids:
        from ..models.relationship_records import StdAnswerExpertAnswerRecord
        for expert_answer_id in expert_answer_ids:
            record = StdAnswerExpertAnswerRecord(
                std_answer_id=std_answer.id,
                expert_answer_id=expert_answer_id,
                created_by=work.created_by
            )
            db.add(record)
    
    # 5. 创建版本问题记录
    version_question = VersionStdQuestion(
        version_work_id=work_id,
        original_question_id=std_question.id,  # 指向新创建的标准问题
        is_modified=False,
        is_new=True,
        is_deleted=False,
        modified_body=qa_data["question"],
        modified_question_type=qa_data.get("question_type", "text")
    )
    db.add(version_question)
    db.flush()

    # 5.1. 写入VersionTag表：合并原始问题tag和qa_data['tags']
    # 先获取所有引用的原始问题ID
    tag_set = set()
    if raw_question_ids:
        from ..models.raw_question import RawQuestion
        for raw_qid in raw_question_ids:
            raw_q = db.query(RawQuestion).filter(RawQuestion.id == raw_qid).first()
            if raw_q and raw_q.tags:
                for tag in raw_q.tags:
                    tag_set.add(tag.label)
                    
    # 再加上qa_data['tags']
    for tag in qa_data.get('tags', []):
        tag_set.add(tag)
        
    # 写入VersionTag表
    from ..models.version_tables import VersionTag
    for tag_label in tag_set:
        version_tag = VersionTag(
            version_work_id=work_id,
            version_question_id=version_question.id,
            tag_label=tag_label,
            is_deleted=False,
            is_new=True
        )
        db.add(version_tag)
    
    # 6. 创建版本答案记录
    version_answer = VersionStdAnswer(
        version_work_id=work_id,
        original_answer_id=std_answer.id,  # 指向新创建的标准答案
        is_modified=False,
        is_deleted=False,
        is_new=True,
        modified_answer=qa_data["answer"],
        modified_answered_by=work.created_by
    )
    db.add(version_answer)
    db.flush()
    
    # 7. 创建版本得分点记录
    scoring_point_ids = []
    if qa_data.get("key_points"):
        for i, point in enumerate(qa_data["key_points"]):
            # 处理point可能是字典或字符串的情况
            if isinstance(point, dict):
                point_content = point.get("answer", "")
            else:
                point_content = str(point)
            
            if point_content.strip():  # 只创建非空的得分点
                scoring_point = StdAnswerScoringPoint(
                    std_answer_id=std_answer.id,
                    answer=point_content.strip(),
                    point_order=i + 1,
                    is_valid=True,
                    answered_by=work.created_by
                )
                db.add(scoring_point)
                db.flush()
                scoring_point_ids.append(scoring_point.id)
    
    for i, point_id in enumerate(scoring_point_ids):
        # 处理point可能是字典或字符串的情况
        point = qa_data["key_points"][i]
        if isinstance(point, dict):
            point_content = point.get("answer", "")
        else:
            point_content = str(point)
        
        version_point = VersionScoringPoint(
            version_work_id=work_id,
            version_answer_id=version_answer.id,
            original_point_id=point_id,
            is_modified=False,
            is_deleted=False,
            is_new=True,
            modified_answer=point_content.strip(),
            modified_point_order=i + 1,
        )
        db.add(version_point)
    
    db.commit()
    
    return {
        "question_id": std_question.id,
        "answer_id": std_answer.id,
        "scoring_point_ids": scoring_point_ids,
        "tag_ids": []  # 暂时返回空列表，因为当前没有处理标签
    }
