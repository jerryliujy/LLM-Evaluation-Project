from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session, joinedload

from ..db.database import get_db
from ..crud import crud_std_question
from ..models.std_question import StdQuestion
from ..models.dataset import Dataset
from ..models.raw_question import RawQuestion
from ..models.tag import Tag
from ..schemas.std_question import StdQuestionCreate, StdQuestionUpdate, StdQuestionResponse
from ..schemas.common import PaginatedResponse
from ..schemas import Msg
from ..auth import get_current_active_user

router = APIRouter(prefix="/api/std-questions", tags=["Standard Questions"])

@router.post("/", response_model=StdQuestionResponse)
def create_std_question(
    std_question: StdQuestionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """创建标准问题"""
    # 验证数据集是否存在
    if not db.query(Dataset).filter(Dataset.id == std_question.dataset_id).first():
        raise HTTPException(status_code=404, detail="Dataset not found")
    db_std_question = StdQuestion(
        dataset_id=std_question.dataset_id,
        body=std_question.body,  # 使用body字段而不是text
        question_type=std_question.question_type,
        is_valid=std_question.is_valid,
        created_by=current_user.id,
        version=std_question.version,
        previous_version_id=std_question.previous_version_id,
        original_version_id=std_question.original_version_id,
        current_version_id=std_question.current_version_id
    )
    db.add(db_std_question)
    db.commit()
    db.refresh(db_std_question)
    
    # 重新查询以获取关联数据
    std_question_with_relations = db.query(StdQuestion).options(
        joinedload(StdQuestion.tags),
        joinedload(StdQuestion.dataset),
        joinedload(StdQuestion.created_by_user)
    ).filter(StdQuestion.id == db_std_question.id).first()
    
    return StdQuestionResponse.from_db_model(std_question_with_relations)

@router.get("/", response_model=PaginatedResponse[StdQuestionResponse])
def read_std_questions_api(
    skip: int = Query(0, ge=0), 
    limit: int = Query(20, ge=1, le=100), 
    include_deleted: bool = Query(False),
    deleted_only: bool = Query(False),
    dataset_id: Optional[int] = Query(None),
    version: Optional[int] = Query(None, description="数据集版本，不指定则使用最新版本"),
    search_query: Optional[str] = Query(None),
    tag_filter: Optional[str] = Query(None),
    question_type_filter: Optional[str] = Query(None),
    scoring_points_filter: Optional[str] = Query(None, description="得分点筛选：has_scoring_points 或 no_scoring_points"),
    db: Session = Depends(get_db)
):
    """获取分页的标准问题列表，支持搜索和筛选"""
    result = crud_std_question.get_std_questions_paginated(
        db, 
        skip=skip, 
        limit=limit, 
        include_deleted=include_deleted, 
        deleted_only=deleted_only,
        dataset_id=dataset_id,
        version=version,
        search_query=search_query,
        tag_filter=tag_filter,
        question_type_filter=question_type_filter,
        scoring_points_filter=scoring_points_filter
    )
    return result

@router.get("/{std_question_id}", response_model=StdQuestionResponse)
def get_std_question(std_question_id: int, db: Session = Depends(get_db)):
    """获取标准问题详情"""
    std_question = db.query(StdQuestion).options(
        joinedload(StdQuestion.dataset),
        joinedload(StdQuestion.raw_question),
        joinedload(StdQuestion.tags),
        joinedload(StdQuestion.created_by_user)  # 加载用户关系
    ).filter(StdQuestion.id == std_question_id).first()
    
    if not std_question:
        raise HTTPException(status_code=404, detail="Standard question not found")
    
    return StdQuestionResponse.from_db_model(std_question)

@router.put("/{std_question_id}", response_model=StdQuestionResponse)
def update_std_question(
    std_question_id: int,
    std_question_update: StdQuestionUpdate,
    db: Session = Depends(get_db)
):
    """更新标准问题"""
    updated_question = crud_std_question.update_std_question(db, std_question_id, std_question_update)
    if not updated_question:
        raise HTTPException(status_code=404, detail="Standard question not found")
      # 重新查询以获取关联数据，包括用户关系
    from sqlalchemy.orm import joinedload
    std_question_with_relations = db.query(StdQuestion).options(
        joinedload(StdQuestion.tags),
        joinedload(StdQuestion.dataset),
        joinedload(StdQuestion.created_by_user)  # 加载用户关系
    ).filter(StdQuestion.id == updated_question.id).first()
    
    return StdQuestionResponse.from_db_model(std_question_with_relations)
    
@router.delete("/{std_question_id}/", response_model=Msg)
def delete_std_question_api(std_question_id: int, db: Session = Depends(get_db)):
    db_question = crud_std_question.set_std_question_deleted_status(db, question_id=std_question_id, deleted_status=True)
    if db_question is None:
        raise HTTPException(status_code=404, detail="StdQuestion not found")
    return Msg(message=f"Standard question {std_question_id} marked as deleted")

@router.post("/{std_question_id}/restore/", response_model=StdQuestionResponse)
def restore_std_question_api(std_question_id: int, db: Session = Depends(get_db)):
    initial_check = crud_std_question.get_std_question(db, question_id=std_question_id, include_deleted=True)
    if not initial_check:
        raise HTTPException(status_code=404, detail="StdQuestion not found")
    if initial_check.is_valid:
        raise HTTPException(status_code=400, detail="StdQuestion is not marked as deleted")
    
    db_question = crud_std_question.set_std_question_deleted_status(db, question_id=std_question_id, deleted_status=False)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Error restoring StdQuestion")
    
    # 重新查询以获取关联数据
    std_question_with_relations = db.query(StdQuestion).options(
        joinedload(StdQuestion.tags),
        joinedload(StdQuestion.dataset),
        joinedload(StdQuestion.created_by_user)
    ).filter(StdQuestion.id == db_question.id).first()
    
    return StdQuestionResponse.from_db_model(std_question_with_relations)

@router.delete("/{std_question_id}/force-delete/", response_model=Msg)
def force_delete_std_question_api(std_question_id: int, db: Session = Depends(get_db)):
    """永久删除标准问题"""
    initial_check = crud_std_question.get_std_question(db, question_id=std_question_id, include_deleted=True)
    if not initial_check:
        raise HTTPException(status_code=404, detail="StdQuestion not found")
    
    if initial_check.is_valid:
        raise HTTPException(status_code=400, detail="StdQuestion must be soft deleted before force deletion")
    
    success = crud_std_question.force_delete_std_question(db, question_id=std_question_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to permanently delete StdQuestion")
    
    return Msg(message=f"Standard question {std_question_id} permanently deleted")

@router.post("/delete-multiple/", response_model=Msg)
def delete_multiple_std_questions_api(question_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    if not question_ids:
        raise HTTPException(status_code=400, detail="No question IDs provided")
    num_deleted = crud_std_question.set_multiple_std_questions_deleted_status(db, question_ids=question_ids, deleted_status=True)
    return Msg(message=f"Successfully marked {num_deleted} standard questions as deleted")

@router.post("/restore-multiple/", response_model=Msg)
def restore_multiple_std_questions_api(question_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    if not question_ids:
        raise HTTPException(status_code=400, detail="No question IDs provided")
    num_restored = crud_std_question.set_multiple_std_questions_deleted_status(db, question_ids=question_ids, deleted_status=False)
    return Msg(message=f"Successfully marked {num_restored} standard questions as not deleted")

@router.get("/{std_question_id}/versions", response_model=List[StdQuestionResponse])
def get_std_question_versions(std_question_id: int, db: Session = Depends(get_db)):
    """获取标准问题的所有版本"""
    # 首先找到目标问题
    target_question = db.query(StdQuestion).filter(StdQuestion.id == std_question_id).first()
    if not target_question:
        raise HTTPException(status_code=404, detail="Standard question not found")
    
    # 找到这个问题链的所有版本
    versions = []
    
    # 向前查找（找到最早的版本）
    earliest = target_question
    while earliest.previous_version_id:
        earliest = db.query(StdQuestion).filter(StdQuestion.id == earliest.previous_version_id).first()
        if not earliest:
            break
    
    # 从最早版本开始，收集所有版本
    current = earliest
    while current:
        versions.append(current)
        # 查找下一个版本
        next_version = db.query(StdQuestion).filter(
            StdQuestion.previous_version_id == current.id
        ).first()
        current = next_version
    
    return sorted(versions, key=lambda x: x.version)

@router.post("/from-raw/{raw_question_id}", response_model=StdQuestionResponse)
def create_std_question_from_raw(
    raw_question_id: int,
    dataset_id: int,
    question_type: str = "single_choice",
    created_by: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """从原始问题创建标准问题"""
    # 验证原始问题存在
    raw_question = db.query(RawQuestion).filter(RawQuestion.id == raw_question_id).first()
    if not raw_question:
        raise HTTPException(status_code=404, detail="Raw question not found")
    
    # 验证数据集存在
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # 使用CRUD函数创建标准问题
    return crud_std_question.create_std_question_from_raw_question(
        db=db,
        raw_question_id=raw_question_id,
        dataset_id=dataset_id,
        question_type=question_type,
        created_by=current_user.id
    )

@router.post("/{std_question_id}/tags")
def add_tags_to_std_question(
    std_question_id: int,
    tag_labels: List[str],
    db: Session = Depends(get_db)
):
    """为标准问题添加标签"""
    std_question = db.query(StdQuestion).filter(StdQuestion.id == std_question_id).first()
    if not std_question:
        raise HTTPException(status_code=404, detail="Standard question not found")
    
    added_tags = []
    for label in tag_labels:
        # 查找或创建标签
        tag = db.query(Tag).filter(Tag.label == label).first()
        if not tag:
            tag = Tag(label=label)
            db.add(tag)
            db.flush()
        
        # 添加关联（如果不存在）
        if tag not in std_question.tags:
            std_question.tags.append(tag)
            added_tags.append(tag.label)
    
    db.commit()
    return {"message": f"Added tags: {added_tags}"}

@router.delete("/{std_question_id}/tags/{tag_label}")
def remove_tag_from_std_question(
    std_question_id: int,
    tag_label: str,
    db: Session = Depends(get_db)
):
    """从标准问题中移除标签"""
    std_question = db.query(StdQuestion).filter(StdQuestion.id == std_question_id).first()
    if not std_question:
        raise HTTPException(status_code=404, detail="Standard question not found")
    
    tag = db.query(Tag).filter(Tag.label == tag_label).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    if tag in std_question.tags:
        std_question.tags.remove(tag)
        db.commit()
        return {"message": f"Removed tag: {tag_label}"}
    else:
        raise HTTPException(status_code=400, detail="Tag not associated with this question")

@router.post("/{std_question_id}/inherit-tags")
def inherit_tags_from_raw_question(
    std_question_id: int,
    db: Session = Depends(get_db)
):
    """从原始问题继承标签到标准问题"""
    std_question = db.query(StdQuestion).options(
        joinedload(StdQuestion.raw_question)
    ).filter(StdQuestion.id == std_question_id).first()
    
    if not std_question:
        raise HTTPException(status_code=404, detail="Standard question not found")
    
    raw_question = std_question.raw_question
    if not raw_question:
        raise HTTPException(status_code=400, detail="No associated raw question found")
    
    inherited_tags = []
    for tag in raw_question.tags:
        if tag not in std_question.tags:
            std_question.tags.append(tag)
            inherited_tags.append(tag.label)
    
    db.commit()
    return {"message": f"Inherited tags: {inherited_tags}"}
