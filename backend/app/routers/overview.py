from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.raw_question import RawQuestion
from app.models.raw_answer import RawAnswer
from app.models.expert_answer import ExpertAnswer
from app.models.std_question import StdQuestion
from app.models.std_answer import StdAnswer

router = APIRouter(prefix="/api/overview", tags=["Overview"])

@router.get("/std-questions")
async def get_std_questions_overview(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    include_invalid: bool = Query(False),
    dataset_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """获取标准问题总览（包含关联的原始问题和标准答案）"""
    
    # 构建查询
    query = db.query(StdQuestion).options(
        joinedload(StdQuestion.raw_question).selectinload(RawQuestion.raw_answers.and_(
            RawAnswer.is_deleted == False
        )).selectinload(RawQuestion.expert_answers.and_(
            ExpertAnswer.is_deleted == False
        )).selectinload(RawQuestion.tags),
        selectinload(StdQuestion.std_answers.and_(
            StdAnswer.is_valid == True if not include_invalid else True
        )),
        joinedload(StdQuestion.dataset)
    )
    
    if not include_invalid:
        query = query.filter(StdQuestion.is_valid == True)
    
    if dataset_id is not None:
        query = query.filter(StdQuestion.dataset_id == dataset_id)
    
    # 只显示最新版本
    if not include_invalid:
        from sqlalchemy import func
        subquery = db.query(
            StdQuestion.raw_question_id,
            StdQuestion.dataset_id,
            func.max(StdQuestion.version).label('max_version')
        ).filter(StdQuestion.is_valid == True).group_by(
            StdQuestion.raw_question_id, StdQuestion.dataset_id
        ).subquery()
        
        query = query.join(subquery, 
            (StdQuestion.raw_question_id == subquery.c.raw_question_id) &
            (StdQuestion.dataset_id == subquery.c.dataset_id) &
            (StdQuestion.version == subquery.c.max_version)
        )
    
    std_questions = query.order_by(StdQuestion.id.desc()).offset(skip).limit(limit).all()
    
    # 格式化返回数据
    result = []
    for std_q in std_questions:
        std_question_data = {
            "id": std_q.id,
            "text": std_q.text,
            "question_type": std_q.question_type,
            "dataset_id": std_q.dataset_id,
            "dataset_description": std_q.dataset.description if std_q.dataset else None,
            "raw_question_id": std_q.raw_question_id,
            "version": std_q.version,
            "created_by": std_q.created_by,
            "created_at": std_q.created_at.isoformat() if std_q.created_at else None,
            "is_valid": std_q.is_valid,
            
            # 关联的原始问题信息
            "raw_question": {
                "id": std_q.raw_question.id,
                "title": std_q.raw_question.title,
                "body": std_q.raw_question.body[:200] + "..." if std_q.raw_question.body and len(std_q.raw_question.body) > 200 else std_q.raw_question.body,
                "author": std_q.raw_question.author,
                "votes": std_q.raw_question.votes,
                "views": std_q.raw_question.views,
                "tags": [tag.label for tag in std_q.raw_question.tags] if std_q.raw_question.tags else [],
                "raw_answers_count": len(std_q.raw_question.raw_answers) if std_q.raw_question.raw_answers else 0,
                "expert_answers_count": len(std_q.raw_question.expert_answers) if std_q.raw_question.expert_answers else 0,
                "is_deleted": std_q.raw_question.is_deleted
            } if std_q.raw_question else None,
            
            # 标准答案
            "std_answers_count": len(std_q.std_answers) if std_q.std_answers else 0,
            "std_answers": [
                {
                    "id": std_a.id,
                    "answer_text": std_a.answer_text[:150] + "..." if std_a.answer_text and len(std_a.answer_text) > 150 else std_a.answer_text,
                    "answer_type": std_a.answer_type,
                    "is_correct": std_a.is_correct,
                    "version": std_a.version,
                    "created_by": std_a.created_by,
                    "is_valid": std_a.is_valid
                }
                for std_a in (std_q.std_answers[:3] if std_q.std_answers else [])
            ]
        }
        result.append(std_question_data)
    
    # 获取总数
    total_query = db.query(StdQuestion)
    if not include_invalid:
        total_query = total_query.filter(StdQuestion.is_valid == True)
    if dataset_id is not None:
        total_query = total_query.filter(StdQuestion.dataset_id == dataset_id)
    total = total_query.count()
    
    return {
        "data": result,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/statistics")
async def get_overview_statistics(db: Session = Depends(get_db)):
    """获取总览统计信息"""
    
    # 原始问题统计
    raw_questions_total = db.query(RawQuestion).filter(RawQuestion.is_deleted == False).count()
    raw_questions_deleted = db.query(RawQuestion).filter(RawQuestion.is_deleted == True).count()
    
    # 原始回答统计
    raw_answers_total = db.query(RawAnswer).filter(RawAnswer.is_deleted == False).count()
    raw_answers_deleted = db.query(RawAnswer).filter(RawAnswer.is_deleted == True).count()
    
    # 专家回答统计
    expert_answers_total = db.query(ExpertAnswer).filter(ExpertAnswer.is_deleted == False).count()
    expert_answers_deleted = db.query(ExpertAnswer).filter(ExpertAnswer.is_deleted == True).count()
    
    # 标准问题统计
    std_questions_total = db.query(StdQuestion).filter(StdQuestion.is_valid == True).count()
    std_questions_invalid = db.query(StdQuestion).filter(StdQuestion.is_valid == False).count()
    
    # 标准答案统计
    std_answers_total = db.query(StdAnswer).filter(StdAnswer.is_valid == True).count()
    std_answers_invalid = db.query(StdAnswer).filter(StdAnswer.is_valid == False).count()
    
    return {
        "raw_questions": {
            "total": raw_questions_total,
            "deleted": raw_questions_deleted
        },
        "raw_answers": {
            "total": raw_answers_total,
            "deleted": raw_answers_deleted
        },
        "expert_answers": {
            "total": expert_answers_total,
            "deleted": expert_answers_deleted
        },
        "std_questions": {
            "total": std_questions_total,
            "invalid": std_questions_invalid
        },
        "std_answers": {
            "total": std_answers_total,
            "invalid": std_answers_invalid
        }
    }
