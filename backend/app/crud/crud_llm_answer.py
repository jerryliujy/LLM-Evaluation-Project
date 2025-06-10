"""
CRUD operations for LLM Answer models
"""
from typing import List, Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_

from ..models.llm_answer import LLM, LLMAnswer, LLMAnswerScoringPoint
from ..schemas.llm_answer import LLMCreate, LLMAnswerCreate, LLMAnswerUpdate


def get_llm(db: Session, llm_id: int) -> Optional[LLM]:
    """获取LLM信息"""
    return db.query(LLM).filter(LLM.id == llm_id).first()


def get_llm_by_name(db: Session, name: str, version: str) -> Optional[LLM]:
    """根据名称和版本获取LLM"""
    return db.query(LLM).filter(
        and_(LLM.name == name, LLM.version == version)
    ).first()


def get_or_create_llm(db: Session, llm_data: LLMCreate) -> LLM:
    """获取或创建LLM"""
    llm = get_llm_by_name(db, llm_data.name, llm_data.version)
    if not llm:
        llm = LLM(**llm_data.model_dump())
        db.add(llm)
        db.commit()
        db.refresh(llm)
    return llm


def get_llms(db: Session, skip: int = 0, limit: int = 100) -> List[LLM]:
    """获取LLM列表"""
    return db.query(LLM).offset(skip).limit(limit).all()


def create_llm_answer(db: Session, answer_data: LLMAnswerCreate) -> LLMAnswer:
    """创建LLM回答"""
    # 提取评分点数据
    scoring_points_data = answer_data.scoring_points
    answer_dict = answer_data.model_dump(exclude={'scoring_points'})
    
    # 创建LLM回答
    llm_answer = LLMAnswer(**answer_dict)
    db.add(llm_answer)
    db.flush()  # 获取ID
    
    # 创建评分点
    for point_data in scoring_points_data:
        scoring_point = LLMAnswerScoringPoint(
            llm_answer_id=llm_answer.id,
            **point_data.model_dump()
        )
        db.add(scoring_point)
    
    db.commit()
    db.refresh(llm_answer)
    return llm_answer


def get_llm_answer(db: Session, answer_id: int) -> Optional[LLMAnswer]:
    """获取LLM回答"""
    return db.query(LLMAnswer).options(
        selectinload(LLMAnswer.scoring_points),
        selectinload(LLMAnswer.llm),
        selectinload(LLMAnswer.std_question)
    ).filter(LLMAnswer.id == answer_id).first()


def get_llm_answers_by_question(
    db: Session, 
    std_question_id: int, 
    include_invalid: bool = False
) -> List[LLMAnswer]:
    """获取某个问题的所有LLM回答"""
    query = db.query(LLMAnswer).options(
        selectinload(LLMAnswer.scoring_points),
        selectinload(LLMAnswer.llm)
    ).filter(LLMAnswer.std_question_id == std_question_id)
    
    if not include_invalid:
        query = query.filter(LLMAnswer.is_valid == True)
    
    return query.all()


def get_llm_answers_by_llm(
    db: Session, 
    llm_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[LLMAnswer]:
    """获取某个LLM的所有回答"""
    return db.query(LLMAnswer).options(
        selectinload(LLMAnswer.scoring_points),
        selectinload(LLMAnswer.std_question)
    ).filter(LLMAnswer.llm_id == llm_id).offset(skip).limit(limit).all()


def update_llm_answer(
    db: Session, 
    answer_id: int, 
    answer_update: LLMAnswerUpdate
) -> Optional[LLMAnswer]:
    """更新LLM回答"""
    llm_answer = db.query(LLMAnswer).filter(LLMAnswer.id == answer_id).first()
    if not llm_answer:
        return None
    
    update_data = answer_update.model_dump(exclude_unset=True, exclude={'scoring_points'})
    for field, value in update_data.items():
        setattr(llm_answer, field, value)
    
    # 更新评分点
    if answer_update.scoring_points is not None:
        # 删除现有评分点
        db.query(LLMAnswerScoringPoint).filter(
            LLMAnswerScoringPoint.llm_answer_id == answer_id
        ).delete()
        
        # 创建新评分点
        for point_data in answer_update.scoring_points:
            scoring_point = LLMAnswerScoringPoint(
                llm_answer_id=answer_id,
                **point_data.model_dump()
            )
            db.add(scoring_point)
    
    db.commit()
    db.refresh(llm_answer)
    return llm_answer


def delete_llm_answer(db: Session, answer_id: int) -> bool:
    """软删除LLM回答"""
    llm_answer = db.query(LLMAnswer).filter(LLMAnswer.id == answer_id).first()
    if not llm_answer:
        return False
    
    llm_answer.is_valid = False
    db.commit()
    return True


def get_llm_answers_paginated(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    llm_id: Optional[int] = None,
    std_question_id: Optional[int] = None,
    include_invalid: bool = False
) -> tuple[List[LLMAnswer], int]:
    """分页获取LLM回答"""
    query = db.query(LLMAnswer).options(
        selectinload(LLMAnswer.scoring_points),
        selectinload(LLMAnswer.llm),
        selectinload(LLMAnswer.std_question)
    )
    
    if llm_id:
        query = query.filter(LLMAnswer.llm_id == llm_id)
    
    if std_question_id:
        query = query.filter(LLMAnswer.std_question_id == std_question_id)
    
    if not include_invalid:
        query = query.filter(LLMAnswer.is_valid == True)
    
    total = query.count()
    answers = query.offset(skip).limit(limit).all()
    
    return answers, total
