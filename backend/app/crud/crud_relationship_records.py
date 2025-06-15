from sqlalchemy.orm import Session
from sqlalchemy import and_, text
from typing import List, Optional
from app.models.relationship_records import (
    StdAnswerRawAnswerRecord,
    StdAnswerExpertAnswerRecord, 
    StdQuestionRawQuestionRecord
)
from app.schemas.relationship_records import (
    StdAnswerRawAnswerRecordCreate,
    StdAnswerExpertAnswerRecordCreate,
    StdQuestionRawQuestionRecordCreate
)

# StdAnswer - RawAnswer 关系操作
def create_std_answer_raw_answer_record(
    db: Session, 
    record: StdAnswerRawAnswerRecordCreate
) -> StdAnswerRawAnswerRecord:
    """创建标准回答-原始回答关系记录"""
    db_record = StdAnswerRawAnswerRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_std_answer_raw_answer_records(
    db: Session,
    std_answer_id: Optional[int] = None,
    raw_answer_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[StdAnswerRawAnswerRecord]:
    """获取标准回答-原始回答关系记录"""
    query = db.query(StdAnswerRawAnswerRecord)
    
    if std_answer_id:
        query = query.filter(StdAnswerRawAnswerRecord.std_answer_id == std_answer_id)
    if raw_answer_id:
        query = query.filter(StdAnswerRawAnswerRecord.raw_answer_id == raw_answer_id)
        
    return query.offset(skip).limit(limit).all()

def delete_std_answer_raw_answer_record(
    db: Session,
    std_answer_id: int,
    raw_answer_id: int
) -> bool:
    """删除标准回答-原始回答关系记录"""
    record = db.query(StdAnswerRawAnswerRecord).filter(
        and_(
            StdAnswerRawAnswerRecord.std_answer_id == std_answer_id,
            StdAnswerRawAnswerRecord.raw_answer_id == raw_answer_id
        )
    ).first()
    
    if record:
        db.delete(record)
        db.commit()
        return True
    return False

# StdAnswer - ExpertAnswer 关系操作
def create_std_answer_expert_answer_record(
    db: Session,
    record: StdAnswerExpertAnswerRecordCreate
) -> StdAnswerExpertAnswerRecord:
    """创建标准回答-专家回答关系记录"""
    db_record = StdAnswerExpertAnswerRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_std_answer_expert_answer_records(
    db: Session,
    std_answer_id: Optional[int] = None,
    expert_answer_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[StdAnswerExpertAnswerRecord]:
    """获取标准回答-专家回答关系记录"""
    query = db.query(StdAnswerExpertAnswerRecord)
    
    if std_answer_id:
        query = query.filter(StdAnswerExpertAnswerRecord.std_answer_id == std_answer_id)
    if expert_answer_id:
        query = query.filter(StdAnswerExpertAnswerRecord.expert_answer_id == expert_answer_id)
        
    return query.offset(skip).limit(limit).all()

def delete_std_answer_expert_answer_record(
    db: Session,
    std_answer_id: int,
    expert_answer_id: int
) -> bool:
    """删除标准回答-专家回答关系记录"""
    record = db.query(StdAnswerExpertAnswerRecord).filter(
        and_(
            StdAnswerExpertAnswerRecord.std_answer_id == std_answer_id,
            StdAnswerExpertAnswerRecord.expert_answer_id == expert_answer_id
        )
    ).first()
    
    if record:
        db.delete(record)
        db.commit()
        return True
    return False

# StdQuestion - RawQuestion 关系操作
def create_std_question_raw_question_record(
    db: Session,
    record: StdQuestionRawQuestionRecordCreate
) -> StdQuestionRawQuestionRecord:
    """创建标准问题-原始问题关系记录"""
    db_record = StdQuestionRawQuestionRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_std_question_raw_question_records(
    db: Session,
    std_question_id: Optional[int] = None,
    raw_question_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[StdQuestionRawQuestionRecord]:
    """获取标准问题-原始问题关系记录"""
    query = db.query(StdQuestionRawQuestionRecord)
    
    if std_question_id:
        query = query.filter(StdQuestionRawQuestionRecord.std_question_id == std_question_id)
    if raw_question_id:
        query = query.filter(StdQuestionRawQuestionRecord.raw_question_id == raw_question_id)
        
    return query.offset(skip).limit(limit).all()

def delete_std_question_raw_question_record(
    db: Session,
    std_question_id: int,
    raw_question_id: int
) -> bool:
    """删除标准问题-原始问题关系记录"""
    record = db.query(StdQuestionRawQuestionRecord).filter(
        and_(
            StdQuestionRawQuestionRecord.std_question_id == std_question_id,
            StdQuestionRawQuestionRecord.raw_question_id == raw_question_id
        )
    ).first()
    
    if record:
        db.delete(record)
        db.commit()
        return True
    return False

# 批量操作
def create_multiple_std_answer_raw_answer_records(
    db: Session,
    std_answer_id: int,
    raw_answer_ids: List[int],
    created_by: Optional[str] = None
) -> List[StdAnswerRawAnswerRecord]:
    """批量创建标准回答-原始回答关系记录"""
    records = []
    for raw_answer_id in raw_answer_ids:
        record = StdAnswerRawAnswerRecord(
            std_answer_id=std_answer_id,
            raw_answer_id=raw_answer_id,
            created_by=created_by
        )
        db.add(record)
        records.append(record)
    
    db.commit()
    for record in records:
        db.refresh(record)
    return records

def create_multiple_std_answer_expert_answer_records(
    db: Session,
    std_answer_id: int,
    expert_answer_ids: List[int],
    created_by: Optional[str] = None
) -> List[StdAnswerExpertAnswerRecord]:
    """批量创建标准回答-专家回答关系记录"""
    records = []
    for expert_answer_id in expert_answer_ids:
        record = StdAnswerExpertAnswerRecord(
            std_answer_id=std_answer_id,
            expert_answer_id=expert_answer_id,
            created_by=created_by
        )
        db.add(record)
        records.append(record)
    
    db.commit()
    for record in records:
        db.refresh(record)
    return records

def create_multiple_std_question_raw_question_records(
    db: Session,
    std_question_id: int,
    raw_question_ids: List[int],
    created_by: Optional[str] = None
) -> List[StdQuestionRawQuestionRecord]:
    """批量创建标准问题-原始问题关系记录"""
    records = []
    for raw_question_id in raw_question_ids:
        record = StdQuestionRawQuestionRecord(
            std_question_id=std_question_id,
            raw_question_id=raw_question_id,
            created_by=created_by
        )
        db.add(record)
        records.append(record)
    
    db.commit()
    for record in records:
        db.refresh(record)
    return records


# ============ Question Tag Relationship Operations ============

def create_question_tag_record(db: Session, std_question_id: int, tag_label: str) -> bool:
    """创建标准问题与标签的关联关系"""
    try:
        # 直接在关联表中插入记录
        db.execute(
            text("INSERT IGNORE INTO QuestionTagRecords (std_question_id, tag_label) VALUES (:std_question_id, :tag_label)"),
            {"std_question_id": std_question_id, "tag_label": tag_label}
        )
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error creating question tag record: {e}")
        return False


def delete_question_tag_record(db: Session, std_question_id: int, tag_label: str) -> bool:
    """删除标准问题与标签的关联关系"""
    try:
        result = db.execute(
            text("DELETE FROM QuestionTagRecords WHERE std_question_id = :std_question_id AND tag_label = :tag_label"),
            {"std_question_id": std_question_id, "tag_label": tag_label}
        )
        db.commit()
        return result.rowcount > 0
    except Exception as e:
        db.rollback()
        print(f"Error deleting question tag record: {e}")
        return False
