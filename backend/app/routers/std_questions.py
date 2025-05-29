from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..db.database import get_db
from ..models.std_question import StdQuestion
from ..models.dataset import Dataset
from ..models.raw_question import RawQuestion
from ..models.tag import Tag
from ..schemas.std_question import StdQuestionCreate, StdQuestionUpdate, StdQuestionResponse

router = APIRouter(prefix="/std-questions", tags=["Standard Questions"])

@router.post("/", response_model=StdQuestionResponse)
def create_std_question(
    std_question: StdQuestionCreate,
    db: Session = Depends(get_db)
):
    """创建标准问题"""
    # 验证dataset和raw_question是否存在
    if not db.query(Dataset).filter(Dataset.id == std_question.dataset_id).first():
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if not db.query(RawQuestion).filter(RawQuestion.id == std_question.raw_question_id).first():
        raise HTTPException(status_code=404, detail="Raw question not found")
    
    # 创建新的标准问题
    db_std_question = StdQuestion(**std_question.dict())
    db.add(db_std_question)
    db.commit()
    db.refresh(db_std_question)
    
    return db_std_question

@router.get("/", response_model=List[StdQuestionResponse])
def list_std_questions(
    dataset_id: Optional[int] = Query(None, description="Filter by dataset ID"),
    is_valid: Optional[bool] = Query(True, description="Filter by validity"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取标准问题列表"""
    query = db.query(StdQuestion).options(
        joinedload(StdQuestion.dataset),
        joinedload(StdQuestion.raw_question)
    )
    
    if dataset_id is not None:
        query = query.filter(StdQuestion.dataset_id == dataset_id)
    
    if is_valid is not None:
        query = query.filter(StdQuestion.is_valid == is_valid)
    
    # 只显示当前有效版本（最新版本）
    if is_valid is True:
        # 通过子查询找到每个问题的最新版本
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
    
    return query.offset(skip).limit(limit).all()

@router.get("/{std_question_id}", response_model=StdQuestionResponse)
def get_std_question(std_question_id: int, db: Session = Depends(get_db)):
    """获取标准问题详情"""
    std_question = db.query(StdQuestion).options(
        joinedload(StdQuestion.dataset),
        joinedload(StdQuestion.raw_question)
    ).filter(StdQuestion.id == std_question_id).first()
    
    if not std_question:
        raise HTTPException(status_code=404, detail="Standard question not found")
    
    return std_question

@router.put("/{std_question_id}", response_model=StdQuestionResponse)
def update_std_question(
    std_question_id: int,
    std_question_update: StdQuestionUpdate,
    db: Session = Depends(get_db)
):
    """更新标准问题（版本控制）"""
    # 获取当前问题
    current_question = db.query(StdQuestion).filter(StdQuestion.id == std_question_id).first()
    if not current_question:
        raise HTTPException(status_code=404, detail="Standard question not found")
    
    # 检查是否有实际修改
    update_data = std_question_update.dict(exclude_unset=True)
    has_changes = False
    for field, value in update_data.items():
        if hasattr(current_question, field) and getattr(current_question, field) != value:
            has_changes = True
            break
    
    if not has_changes:
        return current_question
    
    # 标记当前版本为无效
    current_question.is_valid = False
    
    # 创建新版本
    new_version_data = {
        'dataset_id': current_question.dataset_id,
        'raw_question_id': current_question.raw_question_id,
        'text': current_question.text,
        'question_type': current_question.question_type,
        'created_by': current_question.created_by,
        'version': current_question.version + 1,
        'previous_version_id': current_question.id,
        'is_valid': True
    }
    
    # 应用更新
    new_version_data.update(update_data)
    
    new_question = StdQuestion(**new_version_data)
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    
    return new_question

@router.delete("/{std_question_id}")
def delete_std_question(std_question_id: int, db: Session = Depends(get_db)):
    """软删除标准问题"""
    std_question = db.query(StdQuestion).filter(StdQuestion.id == std_question_id).first()
    if not std_question:
        raise HTTPException(status_code=404, detail="Standard question not found")
    
    std_question.is_valid = False
    db.commit()
    
    return {"message": "Standard question marked as invalid"}

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
    db: Session = Depends(get_db)
):
    """从原始问题创建标准问题"""
    # 验证原始问题存在
    raw_question = db.query(RawQuestion).filter(RawQuestion.id == raw_question_id).first()
    if not raw_question:
        raise HTTPException(status_code=404, detail="Raw question not found")
    
    # 验证数据集存在
    if not db.query(Dataset).filter(Dataset.id == dataset_id).first():
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # 检查是否已存在相同的标准问题
    existing = db.query(StdQuestion).filter(
        StdQuestion.raw_question_id == raw_question_id,
        StdQuestion.dataset_id == dataset_id,
        StdQuestion.is_valid == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Standard question already exists for this raw question in this dataset"
        )
    
    # 创建标准问题
    std_question_data = StdQuestionCreate(
        dataset_id=dataset_id,
        raw_question_id=raw_question_id,
        text=raw_question.title,  # 使用原始问题的标题作为标准问题文本
        question_type=question_type,
        created_by=created_by
    )
    
    return create_std_question(std_question_data, db)

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
