from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from app.db.database import get_db
from app.models.dataset import Dataset
from app.models.user import User
from app.schemas.dataset import DatasetCreate, DatasetUpdate, DatasetResponse, DatasetWithStats
from app.auth import get_current_active_user
from app.crud.crud_dataset import (
    get_datasets_paginated, get_dataset as crud_get_dataset, get_dataset_versions, 
    create_dataset_version, get_latest_dataset_version, delete_dataset
)

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])

@router.post("/", response_model=DatasetResponse)
def create_dataset(
    dataset: DatasetCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建数据集"""
    # 在应用层管理数据集ID分配
    # 获取当前最大的数据集ID
    max_id_result = db.query(func.max(Dataset.id)).scalar()
    next_dataset_id = (max_id_result or 0) + 1
    
    # 新数据集从版本1开始
    version = getattr(dataset, 'version', 1) or 1
    
    db_dataset = Dataset(
        id=next_dataset_id,
        version=version,
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
    show_all_versions: bool = Query(False, description="是否显示所有版本，默认只显示最新版本"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取数据集列表"""
    if show_all_versions:
        # 显示所有版本
        query = db.query(Dataset)
    else:
        # 只显示每个数据集ID的最新版本
        from sqlalchemy import distinct
        
        # 子查询：获取每个数据集ID的最大版本号
        subquery = db.query(
            Dataset.id.label('dataset_id'),
            func.max(Dataset.version).label('max_version')
        ).group_by(Dataset.id).subquery()
        
        # 主查询：获取最新版本的数据集
        query = db.query(Dataset).join(
            subquery,
            and_(
                Dataset.id == subquery.c.dataset_id,
                Dataset.version == subquery.c.max_version
            )
        )
    
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
            ((Dataset.is_public == True) | (Dataset.created_by == current_user_id)) & (Dataset.is_valid == True)
        )
    else:
        query = query.filter((Dataset.is_public == True) & (Dataset.is_valid == True))
    
    datasets = query.order_by(Dataset.create_time.desc()).offset(skip).limit(limit).all()
      # 为每个数据集添加统计信息 - marketplace端点
    result = []
    for dataset in datasets:
        std_questions_count = db.query(func.count(StdQuestion.id)).filter(
            StdQuestion.dataset_id == dataset.id,
            StdQuestion.original_version_id <= dataset.version,
            StdQuestion.current_version_id >= dataset.version,
            StdQuestion.is_valid == True
        ).scalar() or 0
        
        std_answers_count = db.query(func.count(StdAnswer.id)).join(StdQuestion).filter(
            StdQuestion.dataset_id == dataset.id,
            StdQuestion.original_version_id <= dataset.version,
            StdQuestion.current_version_id >= dataset.version,
            StdQuestion.is_valid == True,
            StdAnswer.is_valid == True
        ).scalar() or 0
          # 创建带统计信息的数据集对象
        dataset_with_stats = DatasetWithStats(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            version=dataset.version,  # 添加version字段
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
    
    query = db.query(Dataset).options(joinedload(Dataset.creator)).filter((Dataset.created_by == current_user.id) & (Dataset.is_valid == True))
    
    datasets = query.order_by(Dataset.create_time.desc()).offset(skip).limit(limit).all()      # 为每个数据集添加统计信息 - my端点
    result = []
    for dataset in datasets:
        std_questions_count = db.query(func.count(StdQuestion.id)).filter(
            StdQuestion.dataset_id == dataset.id,
            StdQuestion.original_version_id <= dataset.version,
            StdQuestion.current_version_id >= dataset.version,
            StdQuestion.is_valid == True
        ).scalar() or 0
        
        std_answers_count = db.query(func.count(StdAnswer.id)).join(StdQuestion).filter(
            StdQuestion.dataset_id == dataset.id,
            StdQuestion.original_version_id <= dataset.version,
            StdQuestion.current_version_id >= dataset.version,
            StdQuestion.is_valid == True,
            StdAnswer.is_valid == True
        ).scalar() or 0
          # 创建带统计信息的数据集对象
        dataset_with_stats = DatasetWithStats(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            version=dataset.version,  # 添加version字段
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
def get_dataset(
    dataset_id: int, 
    version: Optional[int] = Query(None, description="数据集版本，不指定则返回最新版本"),
    db: Session = Depends(get_db)
):
    """获取数据集详情"""
    if version is not None:
        # 获取指定版本
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.version == version
        ).first()
    else:
        # 获取最新版本
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).order_by(
            Dataset.version.desc()
        ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return dataset

@router.get("/{dataset_id}/stats")
def get_dataset_stats(
    dataset_id: int, 
    version: Optional[int] = Query(None, description="数据集版本，不指定则使用最新版本"),
    db: Session = Depends(get_db)
):
    """获取数据集统计信息"""
    if version is not None:
        # 获取指定版本
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.version == version
        ).first()
    else:
        # 获取最新版本
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).order_by(
            Dataset.version.desc()
        ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    from ..models.std_question import StdQuestion
    from ..models.std_answer import StdAnswer
    from sqlalchemy import func
    
    # 获取该特定版本数据集的标准问题数量
    std_questions_count = db.query(func.count(StdQuestion.id)).filter(
        StdQuestion.dataset_id == dataset_id,
        StdQuestion.current_version_id == dataset.version,  # 使用特定版本
        StdQuestion.is_valid == True
    ).scalar()
    
    # 获取该特定版本数据集的标准答案数量  
    std_answers_count = db.query(func.count(StdAnswer.id)).join(
        StdQuestion, StdAnswer.std_question_id == StdQuestion.id
    ).filter(
        StdQuestion.dataset_id == dataset_id,
        StdQuestion.current_version_id == dataset.version,  # 使用特定版本
        StdQuestion.is_valid == True,
        StdAnswer.is_valid == True
    ).scalar()
    
    return {
        "dataset_id": dataset_id,
        "version": dataset.version,
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
def delete_dataset_soft(
    dataset_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """软删除数据集（设置is_valid为False）"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # 检查权限：只有数据集创建者可以删除
    if dataset.created_by != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to delete this dataset"
        )
      # 执行软删除
    success = delete_dataset(db, dataset_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete dataset")
    
    return {"message": "Dataset deleted successfully"}

@router.post("/{dataset_id}/restore")
def restore_dataset(
    dataset_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """恢复软删除的数据集（设置is_valid为True）"""
    # 查找已删除的数据集
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.is_valid == False
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Deleted dataset not found")
    
    # 检查权限：只有数据集创建者可以恢复
    if dataset.created_by != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to restore this dataset"
        )
    
    # 执行恢复
    from app.crud.crud_dataset import restore_dataset as crud_restore_dataset
    success = crud_restore_dataset(db, dataset_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to restore dataset")
    
    return {"message": "Dataset restored successfully"}

@router.get("/{dataset_id}/versions", response_model=List[DatasetResponse])
def get_dataset_versions_endpoint(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取数据集的所有版本"""
    versions = get_dataset_versions(db, dataset_id)
    if not versions:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # 检查权限：只有数据集是公开的或者用户是创建者才能查看
    first_version = versions[0]
    if not first_version.is_public and first_version.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to access this dataset")
    
    return versions


@router.post("/{dataset_id}/versions", response_model=DatasetResponse)
def create_new_dataset_version(
    dataset_id: int,
    dataset_update: DatasetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建数据集的新版本"""
    # 检查原数据集是否存在
    original_dataset = db.query(Dataset).filter(Dataset.id == dataset_id).order_by(
        Dataset.version.desc()
    ).first()
    if not original_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # 只有创建者可以创建新版本
    if original_dataset.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only dataset creator can create new versions")
    
    try:
        new_version = create_dataset_version(db, dataset_id, dataset_update, current_user.id)
        return new_version
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{dataset_id}/std-qa", response_model=List[dict])
def get_dataset_std_qa(
    dataset_id: int,
    version: Optional[int] = Query(None, description="数据集版本，不指定则返回最新版本"),
    db: Session = Depends(get_db)
):
    """获取数据集的标准问答对"""
    # 获取数据集
    if version is not None:
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.version == version
        ).first()
    else:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).order_by(
            Dataset.version.desc()
        ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
      # 获取该版本的所有标准问题
    from ..models.std_question import StdQuestion
    from ..models.std_answer import StdAnswer
    from ..models.tag import Tag
    
    questions = db.query(StdQuestion).options(
        joinedload(StdQuestion.std_answers).joinedload(StdAnswer.scoring_points),
        joinedload(StdQuestion.tags)
    ).filter(
        StdQuestion.dataset_id == dataset_id,
        # 使用版本区间查询：数据集版本应该在问题的有效版本区间内
        StdQuestion.original_version_id <= dataset.version,
        StdQuestion.current_version_id >= dataset.version,
        StdQuestion.is_valid == True
    ).all()
    
    result = []
    for question in questions:
        question_data = {
            "id": question.id,
            "body": question.body,
            "question_type": question.question_type,
            "is_valid": question.is_valid,
            "created_at": question.created_at.isoformat() if question.created_at else None,
            "version": question.version,
            "tags": [tag.label for tag in question.tags] if question.tags else [],
            "std_answers": []        
        }
        
        for answer in question.std_answers:
            # 检查答案是否在指定版本的有效区间内
            if (answer.is_valid and 
                answer.original_version_id <= dataset.version and 
                answer.current_version_id >= dataset.version):
                answer_data = {
                    "id": answer.id,
                    "answer": answer.answer,
                    "answered_by": answer.answered_by,
                    "answered_at": answer.answered_at.isoformat() if answer.answered_at else None,
                    "scoring_points": []
                }
                
                if answer.scoring_points:
                    for point in answer.scoring_points:
                        if point.is_valid:
                            answer_data["scoring_points"].append({
                                "id": point.id,
                                "answer": point.answer,
                                "point_order": point.point_order,
                                "answered_by": point.answered_by
                            })
                
                question_data["std_answers"].append(answer_data)
        
        result.append(question_data)
    
    return result

@router.get("/{dataset_id}/versions/{version}/std-answers")
def get_dataset_std_answers_by_version(
    dataset_id: int,
    version: int,
    include_deleted: bool = Query(False, description="Include deleted answers"),
    db: Session = Depends(get_db)
):
    """根据数据集版本获取标准答案"""
    from ..crud.crud_std_answer import get_std_answers_by_dataset_version
    
    # 验证数据集版本是否存在
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.version == version
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=404, 
            detail=f"Dataset {dataset_id} version {version} not found"
        )
    
    # 获取该版本的标准答案
    answers = get_std_answers_by_dataset_version(
        db=db,
        dataset_id=dataset_id,
        dataset_version=version,
        include_deleted=include_deleted
    )
    
    # 格式化返回数据
    result = []
    for answer in answers:
        answer_data = {
            "id": answer.id,
            "std_question_id": answer.std_question_id,
            "answer": answer.answer,
            "is_valid": answer.is_valid,
            "answered_by": answer.answered_by_user.username if answer.answered_by_user else "unknown",
            "answered_at": answer.answered_at.isoformat() if answer.answered_at else None,
            "version": answer.version,
            "original_version_id": answer.original_version_id,
            "current_version_id": answer.current_version_id,
            "std_question": {
                "id": answer.std_question.id,
                "body": answer.std_question.body,
                "question_type": answer.std_question.question_type
            } if answer.std_question else None,
            "scoring_points": []
        }
        
        if answer.scoring_points:
            for point in answer.scoring_points:
                if point.is_valid or include_deleted:
                    answer_data["scoring_points"].append({
                        "id": point.id,
                        "answer": point.answer,
                        "point_order": point.point_order,
                        "is_valid": point.is_valid,
                        "answered_by": point.answered_by_user.username if point.answered_by_user else "unknown"
                    })
        
        result.append(answer_data)
    
    return result
