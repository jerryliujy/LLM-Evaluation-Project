from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.schemas.relationship_records import (
    StdAnswerRawAnswerRecord,
    StdAnswerRawAnswerRecordCreate,
    StdAnswerExpertAnswerRecord,
    StdAnswerExpertAnswerRecordCreate,
    StdQuestionRawQuestionRecord,
    StdQuestionRawQuestionRecordCreate,
    CreateStandardQAWithReferencesRequest
)
from app.schemas.common import Msg
from app.crud import crud_relationship_records
from app.crud import crud_std_question, crud_std_answer

router = APIRouter(
    prefix="/api/relationship-records",
    tags=["Relationship Records"],
    responses={404: {"description": "Not found"}},
)

# 标准回答-原始回答关系
@router.post("/std-answer-raw-answer/", response_model=StdAnswerRawAnswerRecord)
def create_std_answer_raw_answer_record(
    record: StdAnswerRawAnswerRecordCreate,
    db: Session = Depends(get_db)
):
    """创建标准回答-原始回答关系记录"""
    return crud_relationship_records.create_std_answer_raw_answer_record(db, record)

@router.get("/std-answer-raw-answer/", response_model=List[StdAnswerRawAnswerRecord])
def get_std_answer_raw_answer_records(
    std_answer_id: Optional[int] = None,
    raw_answer_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取标准回答-原始回答关系记录"""
    return crud_relationship_records.get_std_answer_raw_answer_records(
        db, std_answer_id=std_answer_id, raw_answer_id=raw_answer_id, skip=skip, limit=limit
    )

@router.delete("/std-answer-raw-answer/{std_answer_id}/{raw_answer_id}/", response_model=Msg)
def delete_std_answer_raw_answer_record(
    std_answer_id: int,
    raw_answer_id: int,
    db: Session = Depends(get_db)
):
    """删除标准回答-原始回答关系记录"""
    success = crud_relationship_records.delete_std_answer_raw_answer_record(
        db, std_answer_id, raw_answer_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="关系记录未找到")
    return Msg(message="关系记录已删除")

# 标准回答-专家回答关系
@router.post("/std-answer-expert-answer/", response_model=StdAnswerExpertAnswerRecord)
def create_std_answer_expert_answer_record(
    record: StdAnswerExpertAnswerRecordCreate,
    db: Session = Depends(get_db)
):
    """创建标准回答-专家回答关系记录"""
    return crud_relationship_records.create_std_answer_expert_answer_record(db, record)

@router.get("/std-answer-expert-answer/", response_model=List[StdAnswerExpertAnswerRecord])
def get_std_answer_expert_answer_records(
    std_answer_id: Optional[int] = None,
    expert_answer_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取标准回答-专家回答关系记录"""
    return crud_relationship_records.get_std_answer_expert_answer_records(
        db, std_answer_id=std_answer_id, expert_answer_id=expert_answer_id, skip=skip, limit=limit
    )

@router.delete("/std-answer-expert-answer/{std_answer_id}/{expert_answer_id}/", response_model=Msg)
def delete_std_answer_expert_answer_record(
    std_answer_id: int,
    expert_answer_id: int,
    db: Session = Depends(get_db)
):
    """删除标准回答-专家回答关系记录"""
    success = crud_relationship_records.delete_std_answer_expert_answer_record(
        db, std_answer_id, expert_answer_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="关系记录未找到")
    return Msg(message="关系记录已删除")

# 标准问题-原始问题关系
@router.post("/std-question-raw-question/", response_model=StdQuestionRawQuestionRecord)
def create_std_question_raw_question_record(
    record: StdQuestionRawQuestionRecordCreate,
    db: Session = Depends(get_db)
):
    """创建标准问题-原始问题关系记录"""
    return crud_relationship_records.create_std_question_raw_question_record(db, record)

@router.get("/std-question-raw-question/", response_model=List[StdQuestionRawQuestionRecord])
def get_std_question_raw_question_records(
    std_question_id: Optional[int] = None,
    raw_question_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取标准问题-原始问题关系记录"""
    return crud_relationship_records.get_std_question_raw_question_records(
        db, std_question_id=std_question_id, raw_question_id=raw_question_id, skip=skip, limit=limit
    )

@router.delete("/std-question-raw-question/{std_question_id}/{raw_question_id}/", response_model=Msg)
def delete_std_question_raw_question_record(
    std_question_id: int,
    raw_question_id: int,
    db: Session = Depends(get_db)
):
    """删除标准问题-原始问题关系记录"""
    success = crud_relationship_records.delete_std_question_raw_question_record(
        db, std_question_id, raw_question_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="关系记录未找到")
    return Msg(message="关系记录已删除")

# 批量操作
@router.post("/std-answer-raw-answer/batch/", response_model=List[StdAnswerRawAnswerRecord])
def create_multiple_std_answer_raw_answer_records(
    std_answer_id: int,
    raw_answer_ids: List[int] = Body(...),
    created_by: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """批量创建标准回答-原始回答关系记录"""
    return crud_relationship_records.create_multiple_std_answer_raw_answer_records(
        db, std_answer_id, raw_answer_ids, created_by
    )

@router.post("/std-answer-expert-answer/batch/", response_model=List[StdAnswerExpertAnswerRecord])
def create_multiple_std_answer_expert_answer_records(
    std_answer_id: int,
    expert_answer_ids: List[int] = Body(...),
    created_by: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """批量创建标准回答-专家回答关系记录"""
    return crud_relationship_records.create_multiple_std_answer_expert_answer_records(
        db, std_answer_id, expert_answer_ids, created_by
    )

@router.post("/std-question-raw-question/batch/", response_model=List[StdQuestionRawQuestionRecord])
def create_multiple_std_question_raw_question_records(
    std_question_id: int,
    raw_question_ids: List[int] = Body(...),
    created_by: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """批量创建标准问题-原始问题关系记录"""
    return crud_relationship_records.create_multiple_std_question_raw_question_records(
        db, std_question_id, raw_question_ids, created_by
    )
