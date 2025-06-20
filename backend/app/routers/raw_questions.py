from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional
from ..crud import crud_raw_question
from ..schemas import RawQuestion, RawQuestionCreate, Msg
from ..schemas.raw_question import RawQuestionWithAnswersCreate, RawQuestionWithAnswersResponse
from ..schemas.common import PaginatedResponse
from ..db.database import get_db
from ..auth import require_admin_or_expert, get_current_active_user
from ..models.user import User
from ..models.raw_question import RawQuestion as RawQuestionModel
from ..models.raw_answer import RawAnswer
from ..models.expert_answer import ExpertAnswer

router = APIRouter(
    prefix="/api/raw_questions",
    tags=["Raw Questions"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=PaginatedResponse[RawQuestion])
def read_raw_questions_api(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    include_deleted: bool = Query(False),
    deleted_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取分页的原始问题列表"""
    result = crud_raw_question.get_raw_questions_paginated(
        db, skip=skip, limit=limit, include_deleted=include_deleted, deleted_only=deleted_only, created_by=current_user.id    )
    return result

@router.post("/with-answers/", response_model=RawQuestionWithAnswersResponse)
def create_raw_question_with_answers_api(
    data: RawQuestionWithAnswersCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建原始问题和相关回答"""
    try:
        # 转换回答数据格式
        answers_data = []
        for answer in data.answers:
            answers_data.append({
                'answer': answer.answer,
                'answered_by': answer.answered_by,
                'upvotes': answer.upvotes,
                'answered_at': answer.answered_at
            })
        
        result = crud_raw_question.create_raw_question_with_answers(
            db=db, 
            question_data=data.question, 
            answers_data=answers_data,
            created_by=current_user.id
        )
        
        return RawQuestionWithAnswersResponse(
            question=result['question'],
            answers=result['answers'],
            success=True,
            message=f"成功创建问题和 {len(result['answers'])} 个回答"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建失败: {str(e)}")

@router.delete("/{question_id}/", response_model=Msg)
def delete_raw_question_api(
    question_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_expert)
):
    db_question = crud_raw_question.set_raw_question_deleted_status(db, question_id=question_id, deleted_status=True)
    if db_question is None:
        raise HTTPException(status_code=404, detail="RawQuestion not found or already processed")
    return Msg(message=f"Raw question {question_id} marked as deleted")

@router.post("/{question_id}/restore/", response_model=RawQuestion)
def restore_raw_question_api(
    question_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_expert)
):
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
def force_delete_raw_question_api(
    question_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_expert)
):
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

@router.put("/{question_id}/", response_model=RawQuestion)
def update_raw_question_api(
    question_id: int,
    question_update: RawQuestionCreate,  
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_expert)
):
    db_question = crud_raw_question.update_raw_question(db, question_id, question_update)
    if db_question is None:
        raise HTTPException(status_code=404, detail="RawQuestion not found")
    return db_question

@router.post("/delete-multiple/", response_model=Msg)
def delete_multiple_raw_questions_api(
    question_ids: List[int] = Body(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_expert)
):
    if not question_ids:
        raise HTTPException(status_code=400, detail="No question IDs provided")
    num_deleted = crud_raw_question.set_multiple_raw_questions_deleted_status(db, question_ids=question_ids, deleted_status=True)
    return Msg(message=f"Successfully marked {num_deleted} raw questions as deleted")

@router.post("/restore-multiple/", response_model=Msg)
def restore_multiple_raw_questions_api(
    question_ids: List[int] = Body(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_expert)
):
    if not question_ids:
        raise HTTPException(status_code=400, detail="No question IDs provided")
    num_restored = crud_raw_question.set_multiple_raw_questions_deleted_status(db, question_ids=question_ids, deleted_status=False)
    return Msg(message=f"Successfully marked {num_restored} raw questions as not deleted")

@router.get("/overview", response_model=dict)
def get_raw_questions_overview_api(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    include_deleted: bool = Query(False),
    deleted_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):    
    """获取原始问题概览，包含所有相关的原始回答和专家回答"""
    # 根据参数决定是否包含已删除的回答
    if include_deleted:
        # 包含已删除的回答
        raw_answers_filter = True  # 不过滤
        expert_answers_filter = True  # 不过滤
    else:
        # 对于已删除的问题，仍然显示所有回答（包括已删除的）以便用户了解完整情况
        # 对于未删除的问题，只显示未删除的回答
        if deleted_only:
            # 如果只显示已删除问题，则显示所有回答（包括已删除的）
            raw_answers_filter = True
            expert_answers_filter = True
        else:
            # 只显示未删除的回答
            raw_answers_filter = RawAnswer.is_deleted == False
            expert_answers_filter = ExpertAnswer.is_deleted == False
            # 只显示未删除的回答
            raw_answers_filter = RawAnswer.is_deleted == False
            expert_answers_filter = ExpertAnswer.is_deleted == False
    
    # 构建查询，预加载相关数据
    query = db.query(RawQuestionModel).options(
        selectinload(RawQuestionModel.raw_answers.and_(raw_answers_filter)),
        selectinload(RawQuestionModel.expert_answers.and_(expert_answers_filter)),
        selectinload(RawQuestionModel.tags)
    )
    
    # 过滤条件
    if not include_deleted and not deleted_only:
        query = query.filter(RawQuestionModel.is_deleted == False)
    elif deleted_only:
        query = query.filter(RawQuestionModel.is_deleted == True)
    
    # 添加用户过滤
    query = query.filter(RawQuestionModel.created_by == current_user.id)
    
    # 获取总数
    total = query.count()
      # 分页
    questions = query.order_by(RawQuestionModel.id.asc()).offset(skip).limit(limit).all()
    
    # 格式化返回数据
    result_data = []
    for question in questions:
        question_data = {
            "id": question.id,
            "title": question.title,
            "body": question.body,
            "author": question.author,
            "url": question.url,
            "view_count": question.views or 0,
            "vote_count": question.votes or 0,
            "issued_at": question.issued_at.isoformat() if question.issued_at else None,
            "created_at": question.created_at.isoformat() if question.created_at else None,
            "is_deleted": question.is_deleted,
            "tags": [tag.label for tag in question.tags] if question.tags else [],            # 原始回答 - 已经在查询中根据参数过滤了
            "raw_answers": [
                {
                    "id": answer.id,
                    "answer": answer.answer,
                    "answered_by": answer.answered_by,
                    "upvotes": answer.upvotes or 0,
                    "answered_at": answer.answered_at.isoformat() if answer.answered_at else None,
                    "is_deleted": answer.is_deleted
                }
                for answer in question.raw_answers
            ],
            
            # 专家回答 - 已经在查询中根据参数过滤了
            "expert_answers": [
                {
                    "id": answer.id,
                    "answer": answer.answer,
                    "answered_by": answer.answered_by,
                    "answered_at": answer.answered_at.isoformat() if answer.answered_at else None,
                    "is_deleted": answer.is_deleted
                }
                for answer in question.expert_answers
            ]
        }
        result_data.append(question_data)
    
    return {
        "data": result_data,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/raw-answers-view", response_model=dict)
def get_raw_answers_view_api(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    include_deleted: bool = Query(False),
    deleted_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取原始回答视图，主要显示原始回答信息"""
      # 构建查询
    query = db.query(RawAnswer).options(
        joinedload(RawAnswer.question).selectinload(RawQuestionModel.tags)
    )
    
    # 过滤条件
    if not include_deleted and not deleted_only:
        query = query.filter(RawAnswer.is_deleted == False)
    elif deleted_only:
        query = query.filter(RawAnswer.is_deleted == True)
    
    # 只显示用户创建的问题的回答
    query = query.join(RawQuestionModel).filter(RawQuestionModel.created_by == current_user.id)
    
    # 获取总数
    total = query.count()
      # 分页
    answers = query.order_by(RawAnswer.id.asc()).offset(skip).limit(limit).all()    # 格式化返回数据
    result_data = []
    for answer in answers:
        answer_data = {
            "id": answer.id,
            "answer": answer.answer,  # 使用与前端一致的字段名
            "answered_by": answer.answered_by,  # 使用与前端一致的字段名
            "upvotes": answer.upvotes or 0,  # 使用与前端一致的字段名
            "answered_at": answer.answered_at.isoformat() if answer.answered_at else None,  # 使用与前端一致的字段名
            "is_deleted": answer.is_deleted,
            "question_id": answer.question_id,  # 使用与前端一致的字段名
            
            # 关联的问题信息
            "question": {
                "id": answer.question.id,  # 使用关系字段
                "title": answer.question.title,
                "author": answer.question.author,
                "tags": [tag.label for tag in answer.question.tags] if answer.question.tags else [],
                "is_deleted": answer.question.is_deleted
            } if answer.question else None
        }
        result_data.append(answer_data)
    
    return {
        "data": result_data,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/expert-answers-view", response_model=dict)
def get_expert_answers_view_api(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    include_deleted: bool = Query(False),
    deleted_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取专家回答视图，主要显示专家回答信息"""
      # 构建查询
    query = db.query(ExpertAnswer).options(
        joinedload(ExpertAnswer.question).selectinload(RawQuestionModel.tags)
    )
    
    # 过滤条件
    if not include_deleted and not deleted_only:
        query = query.filter(ExpertAnswer.is_deleted == False)
    elif deleted_only:
        query = query.filter(ExpertAnswer.is_deleted == True)
    
    # 只显示用户创建的问题的回答
    query = query.join(RawQuestionModel).filter(RawQuestionModel.created_by == current_user.id)
    
    # 获取总数
    total = query.count()
      # 分页
    answers = query.order_by(ExpertAnswer.id.asc()).offset(skip).limit(limit).all()    # 格式化返回数据
    result_data = []
    for answer in answers:
        answer_data = {
            "id": answer.id,
            "answer": answer.answer,  # 使用与前端一致的字段名
            "answered_by": answer.answered_by,     # 使用与前端一致的字段名
            "answered_at": answer.answered_at.isoformat() if answer.answered_at else None,
            "is_deleted": answer.is_deleted,
            "question_id": answer.question_id,  # 使用与前端一致的字段名
            
            # 关联的问题信息
            "question": {
                "id": answer.question.id,    # 使用关系字段
                "title": answer.question.title,
                "author": answer.question.author,
                "tags": [tag.label for tag in answer.question.tags] if answer.question.tags else [],
                "is_deleted": answer.question.is_deleted
            } if answer.question else None
        }
        result_data.append(answer_data)
    
    return {
        "data": result_data,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/search", response_model=dict)
def search_raw_questions_api(
    q: str = Query(..., description="搜索关键词"),
    skip: int = Query(0, ge=0), 
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """搜索原始问题"""
    from sqlalchemy import or_, func
    
    # 构建搜索查询
    query = db.query(RawQuestionModel).options(
        selectinload(RawQuestionModel.raw_answers),
        selectinload(RawQuestionModel.expert_answers),
        selectinload(RawQuestionModel.tags)
    )
    
    # 只搜索用户创建的问题
    query = query.filter(RawQuestionModel.created_by == current_user.id)
    
    # 只搜索未删除的问题
    query = query.filter(RawQuestionModel.is_deleted == False)
    
    # 搜索条件：在标题、内容、作者中搜索
    search_filter = or_(
        func.lower(RawQuestionModel.title).contains(func.lower(q)),
        func.lower(RawQuestionModel.body).contains(func.lower(q)),
        func.lower(RawQuestionModel.author).contains(func.lower(q))
    )
    query = query.filter(search_filter)
    
    # 获取总数
    total = query.count()
    
    # 分页
    questions = query.order_by(RawQuestionModel.id.asc()).offset(skip).limit(limit).all()
    
    # 转换为可序列化的格式
    results = []
    for question in questions:
        question_data = {
            "id": question.id,
            "title": question.title,
            "body": question.body,
            "author": question.author,
            "url": question.url,
            "votes": question.votes,
            "views": question.views,
            "issued_at": question.issued_at.isoformat() if question.issued_at else None,
            "created_at": question.created_at.isoformat() if question.created_at else None,
            "is_deleted": question.is_deleted,
            "tags": [tag.label for tag in question.tags] if question.tags else []
        }
        results.append(question_data)
    
    return {
        "results": results,
        "total": total,
        "skip": skip,
        "limit": limit
    }