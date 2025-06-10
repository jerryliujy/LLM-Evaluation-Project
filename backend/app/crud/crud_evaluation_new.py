"""
Updated CRUD operations for Evaluation model
"""
from typing import List, Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, func

from ..models.evaluation import Evaluation, EvaluatorType
from ..schemas.evaluation import EvaluationCreate, EvaluationUpdate


def get_evaluation(db: Session, evaluation_id: int) -> Optional[Evaluation]:
    """获取单个评估记录"""
    return db.query(Evaluation).options(
        selectinload(Evaluation.std_question),
        selectinload(Evaluation.llm_answer),
        selectinload(Evaluation.evaluator)
    ).filter(Evaluation.id == evaluation_id).first()


def get_evaluations_by_llm_answer(
    db: Session, 
    llm_answer_id: int, 
    evaluator_type: Optional[EvaluatorType] = None,
    include_invalid: bool = False
) -> List[Evaluation]:
    """获取某个LLM回答的所有评估"""
    query = db.query(Evaluation).filter(Evaluation.llm_answer_id == llm_answer_id)
    
    if evaluator_type:
        query = query.filter(Evaluation.evaluator_type == evaluator_type)
    
    if not include_invalid:
        query = query.filter(Evaluation.is_valid == True)
    
    return query.all()


def get_evaluations_by_question(
    db: Session, 
    std_question_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[Evaluation]:
    """获取某个问题的所有评估"""
    return db.query(Evaluation).options(
        selectinload(Evaluation.llm_answer),
        selectinload(Evaluation.evaluator)
    ).filter(Evaluation.std_question_id == std_question_id).offset(skip).limit(limit).all()


def get_evaluations_by_user(
    db: Session, 
    evaluator_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[Evaluation]:
    """获取某个用户的所有评估"""
    return db.query(Evaluation).options(
        selectinload(Evaluation.std_question),
        selectinload(Evaluation.llm_answer)
    ).filter(
        and_(
            Evaluation.evaluator_id == evaluator_id,
            Evaluation.evaluator_type == EvaluatorType.USER
        )
    ).offset(skip).limit(limit).all()


def create_evaluation(db: Session, evaluation: EvaluationCreate) -> Evaluation:
    """创建评估记录"""
    db_evaluation = Evaluation(**evaluation.model_dump())
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
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        return None
    
    update_data = evaluation_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(evaluation, field, value)
    
    db.commit()
    db.refresh(evaluation)
    return evaluation


def delete_evaluation(db: Session, evaluation_id: int) -> bool:
    """软删除评估记录"""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        return False
    
    evaluation.is_valid = False
    db.commit()
    return True


def get_evaluation_statistics(db: Session, llm_answer_id: int) -> dict:
    """获取某个LLM回答的评估统计信息"""
    evaluations = db.query(Evaluation).filter(
        and_(
            Evaluation.llm_answer_id == llm_answer_id,
            Evaluation.is_valid == True
        )
    ).all()
    
    if not evaluations:
        return {
            "total_count": 0,
            "user_count": 0,
            "auto_count": 0,
            "average_score": 0,
            "user_average_score": 0,
            "auto_average_score": 0
        }
    
    user_evaluations = [e for e in evaluations if e.evaluator_type == EvaluatorType.USER]
    auto_evaluations = [e for e in evaluations if e.evaluator_type == EvaluatorType.LLM]
    
    return {
        "total_count": len(evaluations),
        "user_count": len(user_evaluations),
        "auto_count": len(auto_evaluations),
        "average_score": sum(e.score for e in evaluations) / len(evaluations),
        "user_average_score": sum(e.score for e in user_evaluations) / len(user_evaluations) if user_evaluations else 0,
        "auto_average_score": sum(e.score for e in auto_evaluations) / len(auto_evaluations) if auto_evaluations else 0
    }


def get_question_evaluation_summary(db: Session, std_question_id: int) -> dict:
    """获取某个问题的评估汇总"""
    evaluations = db.query(Evaluation).filter(
        and_(
            Evaluation.std_question_id == std_question_id,
            Evaluation.is_valid == True
        )
    ).all()
    
    if not evaluations:
        return {
            "total_evaluations": 0,
            "average_score": 0,
            "llm_answer_count": 0,
            "evaluated_answer_count": 0
        }
    
    # 统计不同LLM回答的数量
    unique_answers = set(e.llm_answer_id for e in evaluations)
    
    return {
        "total_evaluations": len(evaluations),
        "average_score": sum(e.score for e in evaluations) / len(evaluations),
        "llm_answer_count": len(unique_answers),
        "evaluated_answer_count": len(unique_answers)
    }


def batch_create_evaluations(db: Session, evaluations: List[EvaluationCreate]) -> List[Evaluation]:
    """批量创建评估"""
    db_evaluations = []
    for evaluation_data in evaluations:
        db_evaluation = Evaluation(**evaluation_data.model_dump())
        db.add(db_evaluation)
        db_evaluations.append(db_evaluation)
    
    db.commit()
    for evaluation in db_evaluations:
        db.refresh(evaluation)
    
    return db_evaluations
