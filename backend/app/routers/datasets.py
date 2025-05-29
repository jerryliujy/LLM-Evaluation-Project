from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.dataset import Dataset
from ..schemas.dataset import DatasetCreate, DatasetUpdate, DatasetResponse

router = APIRouter(prefix="/datasets", tags=["Datasets"])

@router.post("/", response_model=DatasetResponse)
def create_dataset(
    dataset: DatasetCreate,
    db: Session = Depends(get_db)
):
    """创建数据集"""
    db_dataset = Dataset(**dataset.dict())
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    
    return db_dataset

@router.get("/", response_model=List[DatasetResponse])
def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取数据集列表"""
    return db.query(Dataset).offset(skip).limit(limit).all()

@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """获取数据集详情"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return dataset

@router.put("/{dataset_id}", response_model=DatasetResponse)
def update_dataset(
    dataset_id: int,
    dataset_update: DatasetUpdate,
    db: Session = Depends(get_db)
):
    """更新数据集"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    update_data = dataset_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dataset, field, value)
    
    db.commit()
    db.refresh(dataset)
    
    return dataset

@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """删除数据集"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # 检查是否有关联的标准问题
    from ..models.std_question import StdQuestion
    std_questions_count = db.query(StdQuestion).filter(
        StdQuestion.dataset_id == dataset_id,
        StdQuestion.is_valid == True
    ).count()
    
    if std_questions_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete dataset: {std_questions_count} active standard questions are associated with it"
        )
    
    db.delete(dataset)
    db.commit()
    
    return {"message": "Dataset deleted successfully"}

@router.get("/{dataset_id}/stats")
def get_dataset_stats(dataset_id: int, db: Session = Depends(get_db)):
    """获取数据集统计信息"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    from ..models.std_question import StdQuestion
    from ..models.std_answer import StdAnswer
    from sqlalchemy import func
    
    # 统计标准问题数量
    std_questions_count = db.query(func.count(StdQuestion.id)).filter(
        StdQuestion.dataset_id == dataset_id,
        StdQuestion.is_valid == True
    ).scalar()
    
    # 统计标准答案数量
    std_answers_count = db.query(func.count(StdAnswer.id)).join(
        StdQuestion, StdAnswer.std_question_id == StdQuestion.id
    ).filter(
        StdQuestion.dataset_id == dataset_id,
        StdQuestion.is_valid == True,
        StdAnswer.is_valid == True
    ).scalar()
    
    return {
        "dataset_id": dataset_id,
        "description": dataset.description,
        "create_time": dataset.create_time,
        "std_questions_count": std_questions_count,
        "std_answers_count": std_answers_count
    }
