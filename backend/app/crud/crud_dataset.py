"""
CRUD operations for Dataset model
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Tuple

from ..models.dataset import Dataset
from ..schemas.dataset import DatasetCreate, DatasetUpdate


def get_dataset(db: Session, dataset_id: int, version: Optional[int] = None) -> Optional[Dataset]:
    """获取单个数据集，如果不指定版本则返回最新版本"""
    query = db.query(Dataset).filter(Dataset.id == dataset_id)
    
    if version is not None:
        # 指定版本
        query = query.filter(Dataset.version == version)
    else:
        # 获取最新版本
        query = query.order_by(Dataset.version.desc())
    
    return query.first()


def get_dataset_by_id_version(db: Session, dataset_id: int, version: int) -> Optional[Dataset]:
    """根据ID和版本获取特定的数据集"""
    return db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.version == version
    ).first()


def get_datasets_paginated(
    db: Session,
    skip: int = 0,
    limit: Optional[int] = 20,  # 改为可选参数
    is_public: Optional[bool] = None,
    search_query: Optional[str] = None,
    created_by: Optional[int] = None,
    include_deleted: bool = False  # 添加参数控制是否包含已删除的数据集
) -> Tuple[List[Dataset], int]:
    """分页获取数据集列表（每个数据集ID只返回最新版本）"""
    
    # 子查询：获取每个数据集ID的最大版本号
    max_version_subquery = db.query(
        Dataset.id,
        func.max(Dataset.version).label('max_version')
    ).group_by(Dataset.id).subquery()
    
    # 主查询：只获取最新版本的数据集
    query = db.query(Dataset).join(
        max_version_subquery,
        and_(
            Dataset.id == max_version_subquery.c.id,
            Dataset.version == max_version_subquery.c.max_version
        )
    )
      # 过滤条件
    if not include_deleted:
        query = query.filter(Dataset.is_valid == True)
    
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
    query = query.order_by(Dataset.create_time.desc()).offset(skip)
    if limit is not None:  # 只有当limit不为None时才应用限制
        query = query.limit(limit)
    datasets = query.all()
    
    return datasets, total


def get_next_dataset_id(db: Session) -> int:
    """获取下一个可用的数据集ID"""
    max_id = db.query(func.max(Dataset.id)).scalar()
    return (max_id or 0) + 1


def create_dataset(db: Session, dataset: DatasetCreate, created_by: int) -> Dataset:
    """创建数据集（应用层分配ID）"""
    # 应用层分配ID
    new_id = get_next_dataset_id(db)
    
    db_dataset = Dataset(
        id=new_id,
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
    """软删除数据集（设置is_valid为False）"""
    db_dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.is_valid == True  # 只能删除有效的数据集
    ).first()
    if not db_dataset:
        return False
    
    # 软删除：设置is_valid为False
    db_dataset.is_valid = False
    db.commit()
    return True

def restore_dataset(db: Session, dataset_id: int) -> bool:
    """恢复软删除的数据集（设置is_valid为True）"""
    db_dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.is_valid == False  # 只能恢复已删除的数据集
    ).first()
    if not db_dataset:
        return False
    
    # 恢复：设置is_valid为True
    db_dataset.is_valid = True
    db.commit()
    return True


def get_public_datasets(db: Session, skip: int = 0, limit: int = 20) -> List[Dataset]:
    """获取公开数据集列表"""
    return db.query(Dataset).filter(
        Dataset.is_public == True,
        Dataset.is_valid == True  # 只返回有效的数据集
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
            Dataset.is_valid == True,  # 只搜索有效的数据集
            or_(
                Dataset.name.ilike(search_term),
                Dataset.description.ilike(search_term)
            )
        )
    ).order_by(Dataset.create_time.desc()).offset(skip).limit(limit).all()


def get_dataset_versions(db: Session, dataset_id: int) -> List[Dataset]:
    """获取数据集的所有版本"""
    return db.query(Dataset).filter(
        Dataset.id == dataset_id
    ).order_by(Dataset.version.desc()).all()


def get_latest_dataset_version(db: Session, dataset_id: int) -> Optional[int]:
    """获取数据集的最新版本号"""
    result = db.query(func.max(Dataset.version)).filter(
        Dataset.id == dataset_id
    ).scalar()
    return result


def create_dataset_version(
    db: Session, 
    dataset_id: int, 
    dataset: DatasetUpdate, 
    created_by: int
) -> Dataset:
    """创建数据集的新版本"""
    # 获取最新版本号
    latest_version = get_latest_dataset_version(db, dataset_id)
    if latest_version is None:
        raise ValueError(f"Dataset {dataset_id} not found")
    
    new_version = latest_version + 1
    
    # 创建新版本
    db_dataset = Dataset(
        id=dataset_id,
        version=new_version,
        name=dataset.name,
        description=dataset.description,
        is_public=dataset.is_public,
        created_by=created_by
    )
    
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    return db_dataset
