from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session, joinedload

from ..db.database import get_db
from ..crud import crud_std_answer
from ..models.std_answer import StdAnswer, StdAnswerScoringPoint
from ..models.std_question import StdQuestion
from ..schemas.std_answer import (
    StdAnswerCreate, StdAnswerUpdate, StdAnswerResponse,
    StdAnswerScoringPointCreate, StdAnswerScoringPointResponse
)
from ..schemas.common import PaginatedResponse
from ..schemas import Msg
from ..auth import get_current_active_user

router = APIRouter(prefix="/api/std-answers", tags=["Standard Answers"])

@router.post("/", response_model=StdAnswerResponse)
def create_std_answer(
    std_answer: StdAnswerCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """创建标准答案"""
    # 验证标准问题是否存在
    if not db.query(StdQuestion).filter(StdQuestion.id == std_answer.std_question_id).first():
        raise HTTPException(status_code=404, detail="Standard question not found")
      # 创建标准答案，如果没有指定answered_by则使用当前用户
    answer_data = std_answer.dict()
    if not answer_data.get('answered_by'):
        answer_data['answered_by'] = current_user.id
    
    db_std_answer = StdAnswer(**answer_data)
    db.add(db_std_answer)
    db.commit()
    db.refresh(db_std_answer)
    
    # 重新查询以获取关联数据
    std_answer_with_relations = db.query(StdAnswer).options(
        joinedload(StdAnswer.std_question),
        joinedload(StdAnswer.scoring_points),
        joinedload(StdAnswer.answered_by_user)
    ).filter(StdAnswer.id == db_std_answer.id).first()
    
    return StdAnswerResponse.from_db_model(std_answer_with_relations)

@router.get("/", response_model=PaginatedResponse[StdAnswerResponse])
def read_std_answers_api(
    skip: int = Query(0, ge=0), 
    limit: int = Query(20, ge=1, le=100), 
    include_deleted: bool = Query(False),
    deleted_only: bool = Query(False),
    dataset_id: Optional[int] = Query(None),
    search_query: Optional[str] = Query(None),
    std_question_filter: Optional[str] = Query(None),
    scoring_point_filter: Optional[str] = Query(None),
    scoring_points_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取分页的标准答案列表，支持搜索和筛选"""
    result = crud_std_answer.get_std_answers_paginated(
        db, 
        skip=skip, 
        limit=limit, 
        include_deleted=include_deleted, 
        deleted_only=deleted_only,
        dataset_id=dataset_id,
        search_query=search_query,
        std_question_filter=std_question_filter,
        scoring_point_filter=scoring_point_filter,
        scoring_points_filter=scoring_points_filter
    )
    return result

@router.get("/{std_answer_id}", response_model=StdAnswerResponse)
def get_std_answer(std_answer_id: int, db: Session = Depends(get_db)):
    """获取标准答案详情"""
    std_answer = db.query(StdAnswer).options(
        joinedload(StdAnswer.std_question),
        joinedload(StdAnswer.scoring_points),
        joinedload(StdAnswer.answered_by_user)  # 加载用户关系
    ).filter(StdAnswer.id == std_answer_id).first()
    
    if not std_answer:
        raise HTTPException(status_code=404, detail="Standard answer not found")
    
    return StdAnswerResponse.from_db_model(std_answer)

@router.put("/{std_answer_id}", response_model=StdAnswerResponse)
def update_std_answer(
    std_answer_id: int,
    std_answer_update: StdAnswerUpdate,
    db: Session = Depends(get_db)
):
    """普通编辑：直接更新标准答案，不创建新版本"""
    updated_answer = crud_std_answer.update_std_answer(db, std_answer_id, std_answer_update)
    if not updated_answer:
        raise HTTPException(status_code=404, detail="Standard answer not found")
      # 重新查询以获取关联数据，包括用户关系
    std_answer_with_relations = db.query(StdAnswer).options(
        joinedload(StdAnswer.std_question),
        joinedload(StdAnswer.scoring_points),
        joinedload(StdAnswer.answered_by_user)  # 加载用户关系
    ).filter(StdAnswer.id == updated_answer.id).first()
    
    return StdAnswerResponse.from_db_model(std_answer_with_relations)

@router.delete("/{std_answer_id}/", response_model=Msg)
def delete_std_answer_api(std_answer_id: int, db: Session = Depends(get_db)):
    db_answer = crud_std_answer.set_std_answer_deleted_status(db, answer_id=std_answer_id, deleted_status=True)
    if db_answer is None:
        raise HTTPException(status_code=404, detail="StdAnswer not found")
    return Msg(message=f"Standard answer {std_answer_id} marked as deleted")

@router.post("/{std_answer_id}/restore/", response_model=StdAnswerResponse)
def restore_std_answer_api(std_answer_id: int, db: Session = Depends(get_db)):
    initial_check = crud_std_answer.get_std_answer(db, answer_id=std_answer_id, include_deleted=True)
    if not initial_check:
        raise HTTPException(status_code=404, detail="StdAnswer not found")
    if initial_check.is_valid:
        raise HTTPException(status_code=400, detail="StdAnswer is not marked as deleted")
    
    db_answer = crud_std_answer.set_std_answer_deleted_status(db, answer_id=std_answer_id, deleted_status=False)
    if db_answer is None:
        raise HTTPException(status_code=404, detail="Error restoring StdAnswer")
      # 重新查询以获取关联数据
    std_answer_with_relations = db.query(StdAnswer).options(
        joinedload(StdAnswer.std_question),
        joinedload(StdAnswer.scoring_points),
        joinedload(StdAnswer.answered_by_user)  # 加载用户关系
    ).filter(StdAnswer.id == db_answer.id).first()
    
    return StdAnswerResponse.from_db_model(std_answer_with_relations)

@router.delete("/{std_answer_id}/force-delete/", response_model=Msg)
def force_delete_std_answer_api(std_answer_id: int, db: Session = Depends(get_db)):
    """永久删除标准答案"""
    initial_check = crud_std_answer.get_std_answer(db, answer_id=std_answer_id, include_deleted=True)
    if not initial_check:
        raise HTTPException(status_code=404, detail="StdAnswer not found")
    
    if initial_check.is_valid:
        raise HTTPException(status_code=400, detail="StdAnswer must be soft deleted before force deletion")
    
    success = crud_std_answer.force_delete_std_answer(db, answer_id=std_answer_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to permanently delete StdAnswer")
    
    return Msg(message=f"Standard answer {std_answer_id} permanently deleted")

@router.post("/delete-multiple/", response_model=Msg)
def delete_multiple_std_answers_api(answer_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    if not answer_ids:
        raise HTTPException(status_code=400, detail="No answer IDs provided")
    num_deleted = crud_std_answer.set_multiple_std_answers_deleted_status(db, answer_ids=answer_ids, deleted_status=True)
    return Msg(message=f"Successfully marked {num_deleted} standard answers as deleted")

@router.post("/restore-multiple/", response_model=Msg)
def restore_multiple_std_answers_api(answer_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    if not answer_ids:
        raise HTTPException(status_code=400, detail="No answer IDs provided")
    num_restored = crud_std_answer.set_multiple_std_answers_deleted_status(db, answer_ids=answer_ids, deleted_status=False)
    return Msg(message=f"Successfully marked {num_restored} standard answers as not deleted")

@router.get("/{std_answer_id}/versions", response_model=List[StdAnswerResponse])
def get_std_answer_versions(std_answer_id: int, db: Session = Depends(get_db)):
    """获取标准答案的所有版本"""
    # 首先找到目标答案
    target_answer = db.query(StdAnswer).filter(StdAnswer.id == std_answer_id).first()
    if not target_answer:
        raise HTTPException(status_code=404, detail="Standard answer not found")
    
    # 找到这个答案链的所有版本
    versions = []
    
    # 向前查找（找到最早的版本）
    earliest = target_answer
    while earliest.previous_version_id:
        earliest = db.query(StdAnswer).filter(StdAnswer.id == earliest.previous_version_id).first()
        if not earliest:
            break
    
    # 从最早版本开始，收集所有版本
    current = earliest
    while current:
        versions.append(current)
        # 查找下一个版本
        next_version = db.query(StdAnswer).filter(
            StdAnswer.previous_version_id == current.id
        ).first()
        current = next_version
    
    return sorted(versions, key=lambda x: x.version)

# 评分点相关API
@router.post("/{std_answer_id}/scoring-points", response_model=StdAnswerScoringPointResponse)
def create_scoring_point(
    std_answer_id: int,
    scoring_point: StdAnswerScoringPointCreate,
    db: Session = Depends(get_db)
):
    """为标准答案添加评分点"""
    # 验证标准答案是否存在
    if not db.query(StdAnswer).filter(StdAnswer.id == std_answer_id).first():
        raise HTTPException(status_code=404, detail="Standard answer not found")
    
    # 创建评分点
    db_scoring_point = StdAnswerScoringPoint(
        std_answer_id=std_answer_id,
        **scoring_point.dict()
    )
    db.add(db_scoring_point)
    db.commit()
    db.refresh(db_scoring_point)
    
    return db_scoring_point

@router.get("/{std_answer_id}/scoring-points", response_model=List[StdAnswerScoringPointResponse])
def list_scoring_points(
    std_answer_id: int,
    is_valid: Optional[bool] = Query(None, description="Filter by validity. None returns all points."),
    db: Session = Depends(get_db)
):
    """获取标准答案的评分点列表"""
    query = db.query(StdAnswerScoringPoint).filter(
        StdAnswerScoringPoint.std_answer_id == std_answer_id
    )
    
    if is_valid is not None:
        query = query.filter(StdAnswerScoringPoint.is_valid == is_valid)
    
    return query.order_by(StdAnswerScoringPoint.point_order).all()

@router.put("/scoring-points/{scoring_point_id}", response_model=StdAnswerScoringPointResponse)
def update_scoring_point(
    scoring_point_id: int,
    answer: str,
    point_order: Optional[int] = None,
    created_by: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """更新评分点（版本控制）"""
    # 获取当前评分点
    current_point = db.query(StdAnswerScoringPoint).filter(
        StdAnswerScoringPoint.id == scoring_point_id
    ).first()
    if not current_point:
        raise HTTPException(status_code=404, detail="Scoring point not found")
    
    # 检查是否有实际修改
    has_changes = (current_point.answer != answer or
                  (point_order is not None and current_point.point_order != point_order))
    
    if not has_changes:
        return current_point
    
    # 标记当前版本为无效
    current_point.is_valid = False
    
    # 创建新版本
    new_point = StdAnswerScoringPoint(
        std_answer_id=current_point.std_answer_id,
        answer=answer,
        point_order=point_order if point_order is not None else current_point.point_order,
        previous_version_id=current_point.id,
        is_valid=True
    )
    
    db.add(new_point)
    db.commit()
    db.refresh(new_point)
    
    return new_point

@router.delete("/scoring-points/{scoring_point_id}")
def delete_scoring_point(scoring_point_id: int, db: Session = Depends(get_db)):
    """软删除评分点"""
    scoring_point = db.query(StdAnswerScoringPoint).filter(
        StdAnswerScoringPoint.id == scoring_point_id
    ).first()
    if not scoring_point:
        raise HTTPException(status_code=404, detail="Scoring point not found")
    
    scoring_point.is_valid = False
    db.commit()
    
    return {"message": "Scoring point marked as invalid"}

@router.post("/scoring-points/{scoring_point_id}/restore")
def restore_scoring_point(scoring_point_id: int, db: Session = Depends(get_db)):
    """恢复评分点"""
    scoring_point = db.query(StdAnswerScoringPoint).filter(
        StdAnswerScoringPoint.id == scoring_point_id
    ).first()
    if not scoring_point:
        raise HTTPException(status_code=404, detail="Scoring point not found")
    
    scoring_point.is_valid = True
    db.commit()
    
    return {"message": "Scoring point restored"}

@router.delete("/scoring-points/{scoring_point_id}/force-delete")
def force_delete_scoring_point(scoring_point_id: int, db: Session = Depends(get_db)):
    """强制删除评分点（永久删除）"""
    scoring_point = db.query(StdAnswerScoringPoint).filter(
        StdAnswerScoringPoint.id == scoring_point_id
    ).first()
    if not scoring_point:
        raise HTTPException(status_code=404, detail="Scoring point not found")
    
    # 如果未被软删除，先软删除
    if scoring_point.is_valid:
        scoring_point.is_valid = False
        db.commit()
    
    # 永久删除
    db.delete(scoring_point)
    db.commit()
    
    return {"message": "Scoring point permanently deleted"}
