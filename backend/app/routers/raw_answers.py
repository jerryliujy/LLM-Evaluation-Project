from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import List
from app.crud import crud_raw_answer
from app.schemas import RawAnswer, RawAnswerCreate, Msg
from app.schemas.common import PaginatedResponse
from app.db.database import get_db

router = APIRouter(
    prefix="/api/raw_answers",
    tags=["Raw Answers"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=PaginatedResponse[RawAnswer])
def read_raw_answers_api(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    include_deleted: bool = Query(False),
    deleted_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """获取分页的原始答案列表"""
    result = crud_raw_answer.get_raw_answers_paginated(
        db, skip=skip, limit=limit, include_deleted=include_deleted, deleted_only=deleted_only    )
    return result

@router.post("/", response_model=RawAnswer)
def create_raw_answer_api(answer: RawAnswerCreate, db: Session = Depends(get_db)):
    """创建新的原始回答"""
    return crud_raw_answer.create_raw_answer(db=db, answer=answer)

@router.delete("/{answer_id}/", response_model=Msg)
def delete_raw_answer_api(answer_id: int, db: Session = Depends(get_db)):
    db_answer = crud_raw_answer.set_raw_answer_deleted_status(db, answer_id=answer_id, deleted_status=True)
    if db_answer is None:
        raise HTTPException(status_code=404, detail="RawAnswer not found")
    return Msg(message=f"Raw answer {answer_id} marked as deleted")

@router.post("/{answer_id}/restore/", response_model=RawAnswer)
def restore_raw_answer_api(answer_id: int, db: Session = Depends(get_db)):
    initial_check = crud_raw_answer.get_raw_answer(db, answer_id=answer_id, include_deleted=True)
    if not initial_check:
        raise HTTPException(status_code=404, detail="RawAnswer not found")
    if not initial_check.is_deleted:
        raise HTTPException(status_code=400, detail="RawAnswer is not marked as deleted")

    try:
        db_answer = crud_raw_answer.set_raw_answer_deleted_status(db, answer_id=answer_id, deleted_status=False)
        if db_answer is None:
            raise HTTPException(status_code=404, detail="Error restoring RawAnswer")
        return db_answer
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{answer_id}/force-delete/", response_model=Msg)
def force_delete_raw_answer_api(answer_id: int, db: Session = Depends(get_db)):
    """永久删除原始答案"""
    initial_check = crud_raw_answer.get_raw_answer(db, answer_id=answer_id, include_deleted=True)
    if not initial_check:
        raise HTTPException(status_code=404, detail="RawAnswer not found")
    
    if not initial_check.is_deleted:
        raise HTTPException(status_code=400, detail="RawAnswer must be soft deleted before force deletion")
    
    success = crud_raw_answer.force_delete_raw_answer(db, answer_id=answer_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to permanently delete RawAnswer")
    
    return Msg(message=f"Raw answer {answer_id} permanently deleted")

@router.post("/delete-multiple/", response_model=Msg)
def delete_multiple_raw_answers_api(answer_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    if not answer_ids:
        raise HTTPException(status_code=400, detail="No answer IDs provided")
    num_deleted = crud_raw_answer.set_multiple_raw_answers_deleted_status(db, answer_ids=answer_ids, deleted_status=True)
    return Msg(message=f"Successfully marked {num_deleted} raw answers as deleted")

@router.post("/restore-multiple/", response_model=Msg)
def restore_multiple_raw_answers_api(answer_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    if not answer_ids:
        raise HTTPException(status_code=400, detail="No answer IDs provided")
    try:
        num_restored = crud_raw_answer.set_multiple_raw_answers_deleted_status(db, answer_ids=answer_ids, deleted_status=False)
        return Msg(message=f"Successfully marked {num_restored} raw answers as not deleted")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))