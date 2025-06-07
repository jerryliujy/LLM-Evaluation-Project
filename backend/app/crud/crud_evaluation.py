"""
CRUD operations for Evaluation model
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.evaluation import Evaluation, EvaluatorType
from ..schemas.evaluation import EvaluationCreate, EvaluationUpdate


def get_evaluation(db: Session, evaluation_id: int) -> Optional[Evaluation]:
    """获取单个评估记录"""
    return db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()


def get_evaluations_by_answer(
    db: Session, 
    std_answer_id: int, 
    evaluator_type: Optional[EvaluatorType] = None,
    include_invalid: bool = False
) -> List[Evaluation]:
    """获取某个标准答案的所有评估"""
    query = db.query(Evaluation).filter(Evaluation.std_answer_id == std_answer_id)
    
    if evaluator_type:
        query = query.filter(Evaluation.evaluator_type == evaluator_type)
    
    if not include_invalid:
        query = query.filter(Evaluation.is_valid == True)
    
    return query.order_by(Evaluation.created_at.desc()).all()


def get_evaluations_by_user(
    db: Session, 
    evaluator_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[Evaluation]:
    """获取某个用户的所有评估"""
    return db.query(Evaluation).filter(
        and_(
            Evaluation.evaluator_id == evaluator_id,
            Evaluation.evaluator_type == EvaluatorType.USER,
            Evaluation.is_valid == True
        )
    ).offset(skip).limit(limit).all()


def create_evaluation(db: Session, evaluation: EvaluationCreate) -> Evaluation:
    """创建新的评估记录"""
    db_evaluation = Evaluation(**evaluation.dict())
    db.add(db_evaluation)
    db.commit()
    db.refresh(db_evaluation)
    return db_evaluation


def update_evaluation(
    db: Session, 
    evaluation_id: int, 
    evaluation_update: EvaluationUpdate
) -> Optional[Evaluation]:
    """更新评估记录"""
    db_evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not db_evaluation:
        return None
    
    update_data = evaluation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_evaluation, field, value)
    
    db.commit()
    db.refresh(db_evaluation)
    return db_evaluation


def delete_evaluation(db: Session, evaluation_id: int) -> bool:
    """软删除评估记录"""
    db_evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not db_evaluation:
        return False
    
    db_evaluation.is_valid = False
    db.commit()
    return True


def get_evaluation_statistics(db: Session, std_answer_id: int) -> dict:
    """获取某个标准答案的评估统计信息"""
    evaluations = db.query(Evaluation).filter(
        and_(
            Evaluation.std_answer_id == std_answer_id,
            Evaluation.is_valid == True
        )
    ).all()
    
    if not evaluations:
        return {
            "total_count": 0,
            "user_count": 0,
            "llm_count": 0,
            "average_score": 0,
            "user_average_score": 0,
            "llm_average_score": 0
        }
    
    user_evaluations = [e for e in evaluations if e.evaluator_type == EvaluatorType.USER]
    llm_evaluations = [e for e in evaluations if e.evaluator_type == EvaluatorType.LLM]
    
    return {
        "total_count": len(evaluations),
        "user_count": len(user_evaluations),
        "llm_count": len(llm_evaluations),
        "average_score": sum(e.score for e in evaluations) / len(evaluations),
        "user_average_score": sum(e.score for e in user_evaluations) / len(user_evaluations) if user_evaluations else 0,
        "llm_average_score": sum(e.score for e in llm_evaluations) / len(llm_evaluations) if llm_evaluations else 0
    }