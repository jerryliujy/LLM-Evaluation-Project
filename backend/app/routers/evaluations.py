"""
Evaluation API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..crud import crud_evaluation
from ..schemas.evaluation import EvaluationCreate, EvaluationResponse, EvaluationUpdate
from ..auth import get_current_user
from ..models.user import User

router = APIRouter()


@router.post("/", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
def create_evaluation(
    evaluation: EvaluationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的评估记录"""
    try:
        # 如果是用户评估，设置evaluator_id为当前用户
        if evaluation.evaluator_type.value == "user":
            evaluation.evaluator_id = current_user.id
        
        db_evaluation = crud_evaluation.create_evaluation(db=db, evaluation=evaluation)
        return db_evaluation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建评估失败: {str(e)}"
        )


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
def get_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个评估记录"""
    db_evaluation = crud_evaluation.get_evaluation(db=db, evaluation_id=evaluation_id)
    if not db_evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评估记录未找到"
        )
    return db_evaluation


@router.put("/{evaluation_id}", response_model=EvaluationResponse)
def update_evaluation(
    evaluation_id: int,
    evaluation_update: EvaluationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新评估记录"""
    db_evaluation = crud_evaluation.update_evaluation(
        db=db, 
        evaluation_id=evaluation_id, 
        evaluation_update=evaluation_update
    )
    if not db_evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评估记录未找到"
        )
    return db_evaluation


@router.delete("/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除评估记录"""
    success = crud_evaluation.delete_evaluation(db=db, evaluation_id=evaluation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评估记录未找到"
        )