from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.raw_question import RawQuestion
from app.models.raw_answer import RawAnswer
from app.models.expert_answer import ExpertAnswer
from app.models.std_question import StdQuestion
from app.models.std_answer import StdAnswer
from app.models.relationship_records import StdQuestionRawQuestionRecord, StdAnswerExpertAnswerRecord

router = APIRouter(prefix="/api/overview", tags=["Overview"])

@router.get("/std-questions")
async def get_std_questions_overview(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    include_invalid: bool = Query(False),
    dataset_id: Optional[int] = Query(None),
    search_query: Optional[str] = Query(None, description="搜索查询"),
    tag_filter: Optional[str] = Query(None, description="标签过滤"),
    question_type_filter: Optional[str] = Query(None, description="问题类型过滤"),
    db: Session = Depends(get_db)
):
    """获取标准问题总览（包含关联的原始问题和标准答案）"""
    
    # 构建基础查询 - 通过关系表关联原始问题，并只包含未删除的原始问题
    query = db.query(StdQuestion).join(
        StdQuestionRawQuestionRecord, 
        StdQuestion.id == StdQuestionRawQuestionRecord.std_question_id
    ).join(
        RawQuestion,
        and_(
            StdQuestionRawQuestionRecord.raw_question_id == RawQuestion.id,
            RawQuestion.is_deleted == False  # 只包含未删除的原始问题
        )
    ).options(
        selectinload(StdQuestion.raw_question_records).selectinload(
            StdQuestionRawQuestionRecord.raw_question
        ).selectinload(RawQuestion.raw_answers.and_(
            RawAnswer.is_deleted == False
        )),
        selectinload(StdQuestion.raw_question_records).selectinload(
            StdQuestionRawQuestionRecord.raw_question
        ).selectinload(RawQuestion.expert_answers.and_(
            ExpertAnswer.is_deleted == False
        )),
        selectinload(StdQuestion.raw_question_records).selectinload(
            StdQuestionRawQuestionRecord.raw_question
        ).selectinload(RawQuestion.tags),
        selectinload(StdQuestion.std_answers.and_(
            StdAnswer.is_valid == True if not include_invalid else True
        )),
        joinedload(StdQuestion.dataset)
    )
    
    if not include_invalid:
        query = query.filter(StdQuestion.is_valid == True)
    if dataset_id is not None:
        query = query.filter(StdQuestion.dataset_id == dataset_id)
      # 添加搜索查询过滤
    if search_query:
        search_term = f"%{search_query}%"
        # 需要左外连接标准答案表，以便在搜索中包含标准答案内容
        from sqlalchemy import or_
        query = query.outerjoin(StdAnswer, StdQuestion.id == StdAnswer.std_question_id)
        query = query.filter(
            or_(
                StdQuestion.body.ilike(search_term),
                RawQuestion.title.ilike(search_term),
                RawQuestion.body.ilike(search_term),
                StdAnswer.answer.ilike(search_term)
            )
        )
    
    # 添加问题类型过滤
    if question_type_filter:
        query = query.filter(StdQuestion.question_type.ilike(f"%{question_type_filter}%"))
    
    # 添加标签过滤
    if tag_filter:
        from app.models.tag import Tag
        query = query.join(RawQuestion.tags).filter(Tag.label.ilike(f"%{tag_filter}%"))
    
    # 去重（因为一个标准问题可能关联多个原始问题）
    query = query.distinct()
    
    std_questions = query.order_by(StdQuestion.id.asc()).offset(skip).limit(limit).all()
    
    # 格式化返回数据
    result = []
    for std_q in std_questions:
        # 获取第一个关联的原始问题作为主要原始问题
        primary_raw_question = None
        if std_q.raw_question_records:
            primary_raw_question = std_q.raw_question_records[0].raw_question        # 收集所有关联的原始问题信息
        raw_questions_list = []
        raw_answers_list = []
        expert_answers_list = []
        all_tags = set()  # 收集所有关联原始问题的标签
        
        for record in std_q.raw_question_records:
            raw_q = record.raw_question
            if raw_q and not raw_q.is_deleted:
                # 收集标签信息
                for tag in raw_q.tags:
                    all_tags.add(tag.label)
                
                # 原始问题信息
                raw_questions_list.append({
                    "id": raw_q.id,
                    "title": raw_q.title,
                    "body": raw_q.body,
                    "author": raw_q.author,
                    "tags": [tag.label for tag in raw_q.tags]
                })
                
                # 原始回答信息 - 显示完整内容
                for raw_a in raw_q.raw_answers:
                    if not raw_a.is_deleted:
                        raw_answers_list.append({
                            "id": raw_a.id,
                            "content": raw_a.answer,
                            "author": raw_a.answered_by,
                            "question_id": raw_q.id,
                            "question_title": raw_q.title
                        })                # 专家回答信息 - 只显示已通过关联表正式采纳的专家回答
                for expert_a in raw_q.expert_answers:
                    if not expert_a.is_deleted:
                        # 检查该专家回答是否已被正式采纳（通过 StdAnswerExpertAnswerRecord 关联表）
                        # 只有在关联表中有记录的专家回答才会显示在概览中
                        if std_q.std_answers:
                            for std_answer in std_q.std_answers:
                                if std_answer.is_valid:
                                    # 检查该专家回答是否与当前标准答案有关联记录
                                    relation_exists = db.query(StdAnswerExpertAnswerRecord).filter(
                                        and_(
                                            StdAnswerExpertAnswerRecord.std_answer_id == std_answer.id,
                                            StdAnswerExpertAnswerRecord.expert_answer_id == expert_a.id
                                        )
                                    ).first()
                                    
                                    if relation_exists:
                                        expert_answers_list.append({
                                            "id": expert_a.id,
                                            "content": expert_a.answer,
                                            "author": expert_a.answered_by,
                                            "question_id": raw_q.id,
                                            "question_title": raw_q.title
                                        })
                                        break  # 找到一个关联就足够了，避免重复添加
        
        # 标准答案文本        std_answer_text = ""
        if std_q.std_answers:
            valid_answers = [a for a in std_q.std_answers if a.is_valid]
            if valid_answers:
                std_answer_text = valid_answers[0].answer
        
        std_question_data = {
            "id": std_q.id,
            "text": std_q.body,  # 标准问题文本
            "answer_text": std_answer_text,  # 标准答案文本
            "tags": list(all_tags),  # 从关联的原始问题收集的所有标签
            "raw_questions": "; ".join([f"{q['title']}: {q['body']}" for q in raw_questions_list]) if raw_questions_list else "无关联原始问题",
            "raw_answers": "; ".join([a['content'] for a in raw_answers_list]) if raw_answers_list else "无原始回答",
            "expert_answers": "; ".join([a['content'] for a in expert_answers_list]) if expert_answers_list else "无专家回答",
            "question_type": std_q.question_type,
            
            # 详细数据（用于详情弹窗）
            "raw_questions_detail": raw_questions_list,
            "raw_answers_detail": raw_answers_list,
            "expert_answers_detail": expert_answers_list,
            "dataset_id": std_q.dataset_id,
            "dataset_description": std_q.dataset.description if std_q.dataset else None,
            "created_at": std_q.created_at.isoformat() if std_q.created_at else None,
            "is_valid": std_q.is_valid,
            
            # 额外的统计信息（用于调试）
            "associated_raw_questions_count": len(std_q.raw_question_records),
            "std_answers_count": len(std_q.std_answers) if std_q.std_answers else 0,
        }
        result.append(std_question_data)      # 获取总数 - 只计算有关联原始问题且原始问题未删除的标准问题
    total_query = db.query(StdQuestion).join(
        StdQuestionRawQuestionRecord, 
        StdQuestion.id == StdQuestionRawQuestionRecord.std_question_id
    ).join(
        RawQuestion,
        and_(
            StdQuestionRawQuestionRecord.raw_question_id == RawQuestion.id,
            RawQuestion.is_deleted == False
        )
    )
    
    if not include_invalid:
        total_query = total_query.filter(StdQuestion.is_valid == True)
    if dataset_id is not None:
        total_query = total_query.filter(StdQuestion.dataset_id == dataset_id)
      # 添加与主查询相同的搜索过滤条件
    if search_query:
        search_term = f"%{search_query}%"
        from sqlalchemy import or_
        total_query = total_query.outerjoin(StdAnswer, StdQuestion.id == StdAnswer.std_question_id)
        total_query = total_query.filter(
            or_(
                StdQuestion.body.ilike(search_term),
                RawQuestion.title.ilike(search_term),
                RawQuestion.body.ilike(search_term),
                StdAnswer.answer_text.ilike(search_term)
            )
        )
    
    if question_type_filter:
        total_query = total_query.filter(StdQuestion.question_type.ilike(f"%{question_type_filter}%"))
    
    if tag_filter:
        from app.models.tag import Tag
        total_query = total_query.join(RawQuestion.tags).filter(Tag.label.ilike(f"%{tag_filter}%"))
    
    total = total_query.distinct().count()
    
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
