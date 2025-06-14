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

@router.get("/{answer_id}/", response_model=ExpertAnswer)
def get_expert_answer_api(
    answer_id: int, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取单个专家回答"""
    answer = crud_expert_answer.get_expert_answer(db, answer_id=answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Expert answer not found")
    
    # 检查权限：专家只能查看自己的回答，管理员可以查看所有回答
    if current_user.role == "expert" and answer.answered_by != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own answers")
    elif current_user.role == "admin":
        # 管理员需要验证该回答是否属于自己创建的问题
        from app.models.raw_question import RawQuestion as RawQuestionModel
        question = db.query(RawQuestionModel).filter(RawQuestionModel.id == answer.question_id).first()
        if not question or question.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="You can only view answers to your own questions")
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return answer

@router.put("/{answer_id}/", response_model=ExpertAnswer)
def update_expert_answer_api(
    answer_id: int,
    answer_data: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新专家回答 - 仅专家本人可以更新自己的回答"""
    # 只有专家可以更新回答
    if current_user.role != "expert":
        raise HTTPException(status_code=403, detail="Only experts can update answers")
    
    # 获取现有回答
    existing_answer = crud_expert_answer.get_expert_answer(db, answer_id=answer_id)
    if not existing_answer:
        raise HTTPException(status_code=404, detail="Expert answer not found")
    
    # 检查权限：只有回答者本人可以更新
    if existing_answer.answered_by != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own answers")
    
    # 检查回答是否已被删除
    if existing_answer.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot update deleted answer")
    
    # 更新回答内容
    new_answer_text = answer_data.get("answer")
    if not new_answer_text or not new_answer_text.strip():
        raise HTTPException(status_code=400, detail="Answer content cannot be empty")
    
    # 更新回答
    from datetime import datetime
    existing_answer.answer = new_answer_text.strip()
    existing_answer.answered_at = datetime.now()
    
    try:
        db.commit()
        db.refresh(existing_answer)
        return existing_answer
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update answer: {str(e)}")

@router.delete("/{answer_id}/", response_model=Msg)
def delete_expert_answer_api(
    answer_id: int, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除专家回答（软删除）- 仅专家本人可以删除自己的回答"""
    # 只有专家可以删除回答
    if current_user.role != "expert":
        raise HTTPException(status_code=403, detail="Only experts can delete answers")
    
    # 获取现有回答
    existing_answer = crud_expert_answer.get_expert_answer(db, answer_id=answer_id)
    if not existing_answer:
        raise HTTPException(status_code=404, detail="Expert answer not found")
    
    # 检查权限：只有回答者本人可以删除
    if existing_answer.answered_by != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own answers")
    
    # 执行软删除
    db_answer = crud_expert_answer.set_expert_answer_deleted_status(db, answer_id=answer_id, deleted_status=True)
    if db_answer is None:
        raise HTTPException(status_code=404, detail="ExpertAnswer not found")
    return Msg(message=f"Expert answer {answer_id} marked as deleted")

@router.delete("/{answer_id}", response_model=Msg)
def delete_expert_answer_api_no_slash(
    answer_id: int, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除专家回答（软删除）- 兼容没有结尾斜杠的路径"""
    return delete_expert_answer_api(answer_id, current_user, db)

@router.get("/{answer_id}", response_model=ExpertAnswer)
def get_expert_answer_api_no_slash(
    answer_id: int, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取单个专家回答 - 兼容没有结尾斜杠的路径"""
    return get_expert_answer_api(answer_id, current_user, db)

@router.put("/{answer_id}", response_model=ExpertAnswer)
def update_expert_answer_api_no_slash(
    answer_id: int,
    answer_data: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新专家回答 - 兼容没有结尾斜杠的路径"""
    return update_expert_answer_api(answer_id, answer_data, current_user, db)

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
    
    if current_user.role == "expert":
        # 专家只能搜索自己的回答
        query = query.filter(ExpertAnswerModel.answered_by == current_user.id)
    elif current_user.role == "admin":
        # 管理员只能搜索对其创建问题的回答
        query = query.join(RawQuestionModel).filter(RawQuestionModel.created_by == current_user.id)
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 只搜索未删除的回答
    query = query.filter(ExpertAnswerModel.is_deleted == False)
    
    # 搜索条件：在回答内容中搜索
    search_filter = func.lower(ExpertAnswerModel.answer).contains(func.lower(q))
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