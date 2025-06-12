"""
CRUD operations for Dataset model
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Tuple

from ..models.dataset import Dataset
from ..schemas.dataset import DatasetCreate, DatasetUpdate


def get_dataset(db: Session, dataset_id: int) -> Optional[Dataset]:
    """获取单个数据集"""
    return db.query(Dataset).filter(Dataset.id == dataset_id).first()


def get_datasets_paginated(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    is_public: Optional[bool] = None,
    search_query: Optional[str] = None,
    created_by: Optional[int] = None
) -> Tuple[List[Dataset], int]:
    """分页获取数据集列表"""
    query = db.query(Dataset)
    
    # 过滤条件
    if is_public is not None:
        query = query.filter(Dataset.is_public == is_public)
    
    if created_by is not None:
        query = query.filter(Dataset.created_by == created_by)
    
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            or_(
                Dataset.name.ilike(search_term),
                Dataset.description.ilike(search_term)
            )
        )
    
    # 获取总数
    total = query.count()
    
    # 分页和排序
    datasets = query.order_by(Dataset.create_time.desc()).offset(skip).limit(limit).all()
    
    return datasets, total


def create_dataset(db: Session, dataset: DatasetCreate, created_by: int) -> Dataset:
    """创建数据集"""
    db_dataset = Dataset(
        name=dataset.name,
        description=dataset.description,
        version=dataset.version or 1,
        is_public=dataset.is_public,
        created_by=created_by
    )
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    return db_dataset


def update_dataset(
    db: Session, 
    dataset_id: int, 
    dataset_update: DatasetUpdate
) -> Optional[Dataset]:
    """更新数据集"""
    db_dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not db_dataset:
        return None
    
    update_data = dataset_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_dataset, field, value)
    
    db.commit()
    db.refresh(db_dataset)
    return db_dataset


def delete_dataset(db: Session, dataset_id: int) -> bool:
    """删除数据集"""
    db_dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not db_dataset:
        return False
    
    db.delete(db_dataset)
    db.commit()
    return True


def get_public_datasets(db: Session, skip: int = 0, limit: int = 20) -> List[Dataset]:
    """获取公开数据集列表"""
    return db.query(Dataset).filter(
        Dataset.is_public == True
    ).order_by(Dataset.create_time.desc()).offset(skip).limit(limit).all()


def search_datasets(
    db: Session, 
    query: str, 
    skip: int = 0, 
    limit: int = 20
) -> List[Dataset]:
    """搜索数据集"""
    search_term = f"%{query}%"
    return db.query(Dataset).filter(
        and_(
            Dataset.is_public == True,
            or_(
                Dataset.name.ilike(search_term),
                Dataset.description.ilike(search_term)
            )
        )
    ).order_by(Dataset.create_time.desc()).offset(skip).limit(limit).all()
