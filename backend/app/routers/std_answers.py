from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..db.database import get_db
from ..models.std_answer import StdAnswer, StdAnswerScoringPoint
from ..models.std_question import StdQuestion
from ..schemas.std_answer import (
    StdAnswerCreate, StdAnswerUpdate, StdAnswerResponse,
    StdAnswerScoringPointCreate, StdAnswerScoringPointResponse
)

router = APIRouter(prefix="/std-answers", tags=["Standard Answers"])

@router.post("/", response_model=StdAnswerResponse)
def create_std_answer(
    std_answer: StdAnswerCreate,
    db: Session = Depends(get_db)
):
    """创建标准答案"""
    # 验证标准问题是否存在
    if not db.query(StdQuestion).filter(StdQuestion.id == std_answer.std_question_id).first():
        raise HTTPException(status_code=404, detail="Standard question not found")
    
    # 创建标准答案
    db_std_answer = StdAnswer(**std_answer.dict())
    db.add(db_std_answer)
    db.commit()
    db.refresh(db_std_answer)
    
    return db_std_answer

@router.get("/", response_model=List[StdAnswerResponse])
def list_std_answers(
    std_question_id: Optional[int] = Query(None, description="Filter by standard question ID"),
    is_valid: Optional[bool] = Query(True, description="Filter by validity"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取标准答案列表"""
    query = db.query(StdAnswer).options(
        joinedload(StdAnswer.std_question),
        joinedload(StdAnswer.scoring_points)
    )
    
    if std_question_id is not None:
        query = query.filter(StdAnswer.std_question_id == std_question_id)
    
    if is_valid is not None:
        query = query.filter(StdAnswer.is_valid == is_valid)
    
    # 只显示当前有效版本（最新版本）
    if is_valid is True:
        from sqlalchemy import func
        subquery = db.query(
            StdAnswer.std_question_id,
            func.max(StdAnswer.version).label('max_version')
        ).filter(StdAnswer.is_valid == True).group_by(
            StdAnswer.std_question_id
        ).subquery()
        
        query = query.join(subquery, 
            (StdAnswer.std_question_id == subquery.c.std_question_id) &
            (StdAnswer.version == subquery.c.max_version)
        )
    
    return query.offset(skip).limit(limit).all()

@router.get("/{std_answer_id}", response_model=StdAnswerResponse)
def get_std_answer(std_answer_id: int, db: Session = Depends(get_db)):
    """获取标准答案详情"""
    std_answer = db.query(StdAnswer).options(
        joinedload(StdAnswer.std_question),
        joinedload(StdAnswer.scoring_points)
    ).filter(StdAnswer.id == std_answer_id).first()
    
    if not std_answer:
        raise HTTPException(status_code=404, detail="Standard answer not found")
    
    return std_answer

@router.put("/{std_answer_id}", response_model=StdAnswerResponse)
def update_std_answer(
    std_answer_id: int,
    std_answer_update: StdAnswerUpdate,
    db: Session = Depends(get_db)
):
    """更新标准答案（版本控制）"""
    # 获取当前答案
    current_answer = db.query(StdAnswer).filter(StdAnswer.id == std_answer_id).first()
    if not current_answer:
        raise HTTPException(status_code=404, detail="Standard answer not found")
    
    # 检查是否有实际修改
    update_data = std_answer_update.dict(exclude_unset=True)
    has_changes = False
    for field, value in update_data.items():
        if hasattr(current_answer, field) and getattr(current_answer, field) != value:
            has_changes = True
            break
    
    if not has_changes:
        return current_answer
    
    # 标记当前版本为无效
    current_answer.is_valid = False
    
    # 创建新版本
    new_version_data = {
        'std_question_id': current_answer.std_question_id,
        'answer': current_answer.answer,
        'created_by': current_answer.created_by,
        'version': current_answer.version + 1,
        'previous_version_id': current_answer.id,
        'is_valid': True
    }
    
    # 应用更新
    new_version_data.update(update_data)
    
    new_answer = StdAnswer(**new_version_data)
    db.add(new_answer)
    
    # 如果有评分点，也需要复制到新版本
    scoring_points = db.query(StdAnswerScoringPoint).filter(
        StdAnswerScoringPoint.std_answer_id == current_answer.id,
        StdAnswerScoringPoint.is_valid == True
    ).all()
    
    db.commit()
    db.refresh(new_answer)
    
    # 复制评分点到新版本
    for point in scoring_points:
        new_point = StdAnswerScoringPoint(
            std_answer_id=new_answer.id,
            scoring_point_text=point.scoring_point_text,
            point_order=point.point_order,
            created_by=point.created_by,
            version=1,  # 新答案的评分点从版本1开始
            is_valid=True
        )
        db.add(new_point)
    
    db.commit()
    db.refresh(new_answer)
    
    return new_answer

@router.delete("/{std_answer_id}")
def delete_std_answer(std_answer_id: int, db: Session = Depends(get_db)):
    """软删除标准答案"""
    std_answer = db.query(StdAnswer).filter(StdAnswer.id == std_answer_id).first()
    if not std_answer:
        raise HTTPException(status_code=404, detail="Standard answer not found")
    
    std_answer.is_valid = False
    
    # 同时标记相关的评分点为无效
    scoring_points = db.query(StdAnswerScoringPoint).filter(
        StdAnswerScoringPoint.std_answer_id == std_answer_id
    ).all()
    
    for point in scoring_points:
        point.is_valid = False
    
    db.commit()
    
    return {"message": "Standard answer and its scoring points marked as invalid"}

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
    is_valid: Optional[bool] = Query(True, description="Filter by validity"),
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
    scoring_point_text: str,
    point_order: Optional[int] = None,
    created_by: Optional[str] = None,
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
    has_changes = (current_point.scoring_point_text != scoring_point_text or
                  (point_order is not None and current_point.point_order != point_order))
    
    if not has_changes:
        return current_point
    
    # 标记当前版本为无效
    current_point.is_valid = False
    
    # 创建新版本
    new_point = StdAnswerScoringPoint(
        std_answer_id=current_point.std_answer_id,
        scoring_point_text=scoring_point_text,
        point_order=point_order if point_order is not None else current_point.point_order,
        created_by=created_by or current_point.created_by,
        version=current_point.version + 1,
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
