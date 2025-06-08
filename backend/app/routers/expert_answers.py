from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import List
from app.crud import crud_expert_answer
from app.schemas import ExpertAnswer, Msg
from app.schemas.common import PaginatedResponse
from app.db.database import get_db
from app.models.user import User
from app.models.expert_answer import ExpertAnswer as ExpertAnswerModel
from app.auth import get_current_active_user

router = APIRouter(
    prefix="/api/expert_answers",
    tags=["Expert Answers"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=PaginatedResponse[ExpertAnswer])
def read_expert_answers_api(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    include_deleted: bool = Query(False),
    deleted_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """获取分页的专家答案列表"""
    result = crud_expert_answer.get_expert_answers_paginated(
        db, skip=skip, limit=limit, include_deleted=include_deleted, deleted_only=deleted_only
    )
    return result

@router.delete("/{answer_id}/", response_model=Msg)
def delete_expert_answer_api(answer_id: int, db: Session = Depends(get_db)):
    db_answer = crud_expert_answer.set_expert_answer_deleted_status(db, answer_id=answer_id, deleted_status=True)
    if db_answer is None:
        raise HTTPException(status_code=404, detail="ExpertAnswer not found")
    return Msg(message=f"Expert answer {answer_id} marked as deleted")

@router.post("/{answer_id}/restore/", response_model=ExpertAnswer)
def restore_expert_answer_api(answer_id: int, db: Session = Depends(get_db)):
    initial_check = crud_expert_answer.get_expert_answer(db, answer_id=answer_id, include_deleted=True)
    if not initial_check:
        raise HTTPException(status_code=404, detail="ExpertAnswer not found")
    if not initial_check.is_deleted:
        raise HTTPException(status_code=400, detail="ExpertAnswer is not marked as deleted")
    
    try:
        db_answer = crud_expert_answer.set_expert_answer_deleted_status(db, answer_id=answer_id, deleted_status=False)
        if db_answer is None:
            raise HTTPException(status_code=404, detail="Error restoring ExpertAnswer")
        return db_answer
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{answer_id}/force-delete/", response_model=Msg)
def force_delete_expert_answer_api(answer_id: int, db: Session = Depends(get_db)):
    """永久删除专家答案"""
    initial_check = crud_expert_answer.get_expert_answer(db, answer_id=answer_id, include_deleted=True)
    if not initial_check:
        raise HTTPException(status_code=404, detail="ExpertAnswer not found")
    
    if not initial_check.is_deleted:
        raise HTTPException(status_code=400, detail="ExpertAnswer must be soft deleted before force deletion")
    
    success = crud_expert_answer.force_delete_expert_answer(db, answer_id=answer_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to permanently delete ExpertAnswer")
    
    return Msg(message=f"Expert answer {answer_id} permanently deleted")

@router.post("/delete-multiple/", response_model=Msg)
def delete_multiple_expert_answers_api(answer_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    if not answer_ids:
        raise HTTPException(status_code=400, detail="No answer IDs provided")
    num_deleted = crud_expert_answer.set_multiple_expert_answers_deleted_status(db, answer_ids=answer_ids, deleted_status=True)
    return Msg(message=f"Successfully marked {num_deleted} expert answers as deleted")

@router.post("/restore-multiple/", response_model=Msg)
def restore_multiple_expert_answers_api(answer_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    if not answer_ids:
        raise HTTPException(status_code=400, detail="No answer IDs provided")
    try:
        num_restored = crud_expert_answer.set_multiple_expert_answers_deleted_status(db, answer_ids=answer_ids, deleted_status=False)
        return Msg(message=f"Successfully marked {num_restored} expert answers as not deleted")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search", response_model=dict)
def search_expert_answers_api(
    q: str = Query(..., description="搜索关键词"),
    skip: int = Query(0, ge=0), 
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """搜索专家答案"""
    from sqlalchemy import or_, func
    from sqlalchemy.orm import joinedload
    from ..models.raw_question import RawQuestion as RawQuestionModel
    
    # 构建搜索查询
    query = db.query(ExpertAnswerModel).options(
        joinedload(ExpertAnswerModel.question)
    )
    
    # 只搜索用户创建的问题的专家回答
    query = query.join(RawQuestionModel).filter(RawQuestionModel.created_by == current_user.id)
    
    # 只搜索未删除的回答
    query = query.filter(ExpertAnswerModel.is_deleted == False)
    
    # 搜索条件：在回答内容、回答者中搜索
    search_filter = or_(
        func.lower(ExpertAnswerModel.answer).contains(func.lower(q)),
        func.lower(ExpertAnswerModel.answered_by).contains(func.lower(q))
    )
    query = query.filter(search_filter)
    
    # 获取总数
    total = query.count()
    
    # 分页
    answers = query.order_by(ExpertAnswerModel.id.asc()).offset(skip).limit(limit).all()
    
    # 转换为可序列化的格式
    results = []
    for answer in answers:
        answer_data = {
            "id": answer.id,
            "answer": answer.answer,
            "answered_by": answer.answered_by,
            "answered_at": answer.answered_at.isoformat() if answer.answered_at else None,
            "is_deleted": answer.is_deleted,
            "question_id": answer.question_id,
            "question": {
                "id": answer.question.id,
                "title": answer.question.title,
                "author": answer.question.author,
                "is_deleted": answer.question.is_deleted
            } if answer.question else None
        }
        results.append(answer_data)
    
    return {
        "results": results,
        "total": total,
        "skip": skip,
        "limit": limit
    }