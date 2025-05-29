from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from ..db.database import get_db
from ..models.tag import Tag
from ..models.raw_question import RawQuestion
from ..models.std_question import StdQuestion
from ..schemas.tag import TagCreate, TagResponse, TagWithQuestionsResponse

router = APIRouter(prefix="/tags", tags=["Tags"])

@router.post("/", response_model=TagResponse)
def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    """创建标签"""
    # 检查标签是否已存在
    existing_tag = db.query(Tag).filter(Tag.label == tag.label).first()
    if existing_tag:
        raise HTTPException(status_code=400, detail="Tag already exists")
    
    db_tag = Tag(label=tag.label)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    
    return db_tag

@router.get("/", response_model=List[TagResponse])
def list_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取标签列表"""
    tags = db.query(Tag).offset(skip).limit(limit).all()
    return tags

@router.get("/{tag_label}", response_model=TagWithQuestionsResponse)
def get_tag_with_questions(tag_label: str, db: Session = Depends(get_db)):
    """获取标签及其关联的问题"""
    tag = db.query(Tag).options(
        joinedload(Tag.raw_questions),
        joinedload(Tag.std_questions)
    ).filter(Tag.label == tag_label).first()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return tag

@router.delete("/{tag_label}")
def delete_tag(tag_label: str, db: Session = Depends(get_db)):
    """删除标签"""
    tag = db.query(Tag).filter(Tag.label == tag_label).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    db.delete(tag)
    db.commit()
    
    return {"message": "Tag deleted successfully"}

@router.post("/batch-create", response_model=List[TagResponse])
def batch_create_tags(tag_labels: List[str], db: Session = Depends(get_db)):
    """批量创建标签"""
    created_tags = []
    for label in tag_labels:
        # 检查是否已存在
        existing_tag = db.query(Tag).filter(Tag.label == label).first()
        if not existing_tag:
            new_tag = Tag(label=label)
            db.add(new_tag)
            created_tags.append(new_tag)
    
    db.commit()
    
    # 刷新所有新创建的标签
    for tag in created_tags:
        db.refresh(tag)
    
    return created_tags

@router.get("/stats/usage")
def get_tag_usage_stats(db: Session = Depends(get_db)):
    """获取标签使用统计"""
    # 统计每个标签被原始问题和标准问题使用的次数
    raw_question_counts = db.query(
        Tag.label,
        func.count(RawQuestion.id).label('raw_question_count')
    ).outerjoin(Tag.raw_questions).group_by(Tag.label).subquery()
    
    std_question_counts = db.query(
        Tag.label,
        func.count(StdQuestion.id).label('std_question_count')
    ).outerjoin(Tag.std_questions).group_by(Tag.label).subquery()
    
    results = db.query(
        Tag.label,
        raw_question_counts.c.raw_question_count,
        std_question_counts.c.std_question_count
    ).outerjoin(
        raw_question_counts, Tag.label == raw_question_counts.c.label
    ).outerjoin(
        std_question_counts, Tag.label == std_question_counts.c.label
    ).all()
    
    return [
        {
            "label": result.label,
            "raw_question_count": result.raw_question_count or 0,
            "std_question_count": result.std_question_count or 0,
            "total_count": (result.raw_question_count or 0) + (result.std_question_count or 0)
        }
        for result in results
    ]
