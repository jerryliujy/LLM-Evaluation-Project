from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from app.db.database import get_db
from app.models.dataset import Dataset
from app.models.user import User
from app.schemas.dataset import DatasetCreate, DatasetUpdate, DatasetResponse, DatasetWithStats
from app.auth import get_current_active_user

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])

@router.post("/", response_model=DatasetResponse)
def create_dataset(
    dataset: DatasetCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建数据集"""
    db_dataset = Dataset(
        name=dataset.name,
        description=dataset.description,
        created_by=current_user.id,
        is_public=dataset.is_public
    )
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    
    return db_dataset

@router.get("/", response_model=List[DatasetResponse])
def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    created_by_id: Optional[int] = Query(None),
    public_only: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取数据集列表"""
    query = db.query(Dataset)
    
    # 如果不是管理员，只能看到公开的数据集或自己的数据集
    if current_user.role != "admin":
        query = query.filter(
            and_(
                Dataset.is_public == True,
                Dataset.created_by == current_user.id
            ) if not public_only else Dataset.is_public == True
        )
    elif public_only:
        query = query.filter(Dataset.is_public == True)
    
    if created_by_id:
        query = query.filter(Dataset.created_by == created_by_id)
    
    return query.order_by(Dataset.create_time.desc()).offset(skip).limit(limit).all()

@router.get("/marketplace", response_model=List[DatasetWithStats])
def get_datasets_marketplace(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """获取数据库市场列表（包含统计信息）"""
    from ..models.raw_question import RawQuestion
    from ..models.std_question import StdQuestion
    from ..models.std_answer import StdAnswer
    
    # 基础查询，包含创建者信息
    query = db.query(Dataset).options(joinedload(Dataset.creator))
    
    # 只显示公开的数据集，或者当前用户的数据集
    if current_user_id:
        query = query.filter(
            (Dataset.is_public == True) | (Dataset.created_by == current_user_id)
        )
    else:
        query = query.filter(Dataset.is_public == True)
    
    datasets = query.order_by(Dataset.create_time.desc()).offset(skip).limit(limit).all()
    
    # 为每个数据集添加统计信息
    result = []
    for dataset in datasets:
        std_questions_count = db.query(func.count(StdQuestion.id)).filter(
            StdQuestion.current_dataset_id == dataset.id,
            StdQuestion.is_valid == True
        ).scalar() or 0
        
        std_answers_count = db.query(func.count(StdAnswer.id)).join(StdQuestion).filter(
            StdQuestion.current_dataset_id == dataset.id,
            StdQuestion.is_valid == True,
            StdAnswer.is_valid == True
        ).scalar() or 0
        
        # 创建带统计信息的数据集对象
        dataset_with_stats = DatasetWithStats(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            created_by=dataset.created_by,
            is_public=dataset.is_public,
            create_time=dataset.create_time,
            std_questions_count=std_questions_count,
            std_answers_count=std_answers_count,
            creator_username=dataset.creator.username if dataset.creator else None
        )
        result.append(dataset_with_stats)
    return result

@router.get("/my", response_model=List[DatasetWithStats])
def get_my_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取自建数据库列表（包含统计信息）"""
    from ..models.raw_question import RawQuestion
    from ..models.std_question import StdQuestion
    from ..models.std_answer import StdAnswer
    
    query = db.query(Dataset).options(joinedload(Dataset.creator)).filter(Dataset.created_by == current_user.id)
    
    datasets = query.order_by(Dataset.create_time.desc()).offset(skip).limit(limit).all()
    
    # 为每个数据集添加统计信息
    result = []
    for dataset in datasets:
        std_questions_count = db.query(func.count(StdQuestion.id)).filter(
            StdQuestion.current_dataset_id == dataset.id,
            StdQuestion.is_valid == True
        ).scalar() or 0
        
        std_answers_count = db.query(func.count(StdAnswer.id)).join(StdQuestion).filter(
            StdQuestion.current_dataset_id == dataset.id,
            StdQuestion.is_valid == True,
            StdAnswer.is_valid == True
        ).scalar() or 0
        
        # 创建带统计信息的数据集对象
        dataset_with_stats = DatasetWithStats(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            created_by=dataset.created_by,
            is_public=dataset.is_public,
            create_time=dataset.create_time,
            std_questions_count=std_questions_count,
            std_answers_count=std_answers_count,
            creator_username=dataset.creator.username if dataset.creator else None
        )
        result.append(dataset_with_stats)
    
    return result

@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """获取数据集详情"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return dataset

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
        StdQuestion.current_dataset_id == dataset_id,
        StdQuestion.is_valid == True
    ).scalar()
    
    # 统计标准答案数量
    std_answers_count = db.query(func.count(StdAnswer.id)).join(
        StdQuestion, StdAnswer.std_question_id == StdQuestion.id
    ).filter(
        StdQuestion.current_dataset_id == dataset_id,
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
        StdQuestion.current_dataset_id == dataset_id,
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
