from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import List
from ..crud import crud_raw_question
from ..schemas import RawQuestion, Msg
from ..schemas.common import PaginatedResponse
from ..db.database import get_db

router = APIRouter(
    prefix="/api/raw_questions",
    tags=["Raw Questions"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=PaginatedResponse[RawQuestion])
def read_raw_questions_api(
    skip: int = Query(0, ge=0), 
    limit: int = Query(20, ge=1, le=100), 
    include_deleted: bool = Query(False),
    deleted_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """获取分页的原始问题列表"""
    result = crud_raw_question.get_raw_questions_paginated(
        db, skip=skip, limit=limit, include_deleted=include_deleted, deleted_only=deleted_only
    )
    return result

@router.delete("/{question_id}/", response_model=Msg)
def delete_raw_question_api(question_id: int, db: Session = Depends(get_db)):
    db_question = crud_raw_question.set_raw_question_deleted_status(db, question_id=question_id, deleted_status=True)
    if db_question is None:
        raise HTTPException(status_code=404, detail="RawQuestion not found or already processed")
    return Msg(message=f"Raw question {question_id} marked as deleted")

@router.post("/{question_id}/restore/", response_model=RawQuestion)
def restore_raw_question_api(question_id: int, db: Session = Depends(get_db)):
    initial_check = crud_raw_question.get_raw_question_including_deleted(db, question_id=question_id)
    if not initial_check:
        raise HTTPException(status_code=404, detail="RawQuestion not found")
    if not initial_check.is_deleted:
        raise HTTPException(status_code=400, detail="RawQuestion is not marked as deleted")

    db_question = crud_raw_question.set_raw_question_deleted_status(db, question_id=question_id, deleted_status=False)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Error restoring RawQuestion")
    return db_question

@router.delete("/{question_id}/force-delete/", response_model=Msg)
def force_delete_raw_question_api(question_id: int, db: Session = Depends(get_db)):
    """永久删除原始问题"""
    initial_check = crud_raw_question.get_raw_question_including_deleted(db, question_id=question_id)
    if not initial_check:
        raise HTTPException(status_code=404, detail="RawQuestion not found")
    
    if not initial_check.is_deleted:
        raise HTTPException(status_code=400, detail="RawQuestion must be soft deleted before force deletion")
    
    success = crud_raw_question.force_delete_raw_question(db, question_id=question_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to permanently delete RawQuestion")
    
    return Msg(message=f"Raw question {question_id} permanently deleted")

@router.post("/delete-multiple/", response_model=Msg)
def delete_multiple_raw_questions_api(question_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    if not question_ids:
        raise HTTPException(status_code=400, detail="No question IDs provided")
    num_deleted = crud_raw_question.set_multiple_raw_questions_deleted_status(db, question_ids=question_ids, deleted_status=True)
    return Msg(message=f"Successfully marked {num_deleted} raw questions as deleted")

@router.post("/restore-multiple/", response_model=Msg)
def restore_multiple_raw_questions_api(question_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    if not question_ids:
        raise HTTPException(status_code=400, detail="No question IDs provided")
    num_restored = crud_raw_question.set_multiple_raw_questions_deleted_status(db, question_ids=question_ids, deleted_status=False)
    return Msg(message=f"Successfully marked {num_restored} raw questions as not deleted")