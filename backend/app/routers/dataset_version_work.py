"""
Dataset Version Work Router
Provides version management capabilities for datasets
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.schemas.dataset_version_work import (
    DatasetVersionWorkCreate, DatasetVersionWorkUpdate, DatasetVersionWorkResponse,
    DatasetVersionWorkSummary, VersionStdQuestionCreate, VersionStdQuestionUpdate,
    VersionStdQuestionResponse, VersionStdAnswerCreate, VersionStdAnswerUpdate,
    VersionStdAnswerResponse, VersionTagCreate, VersionTagResponse,
    WorkStatus
)
from app.crud.crud_dataset_version_work import (
    create_dataset_version_work, get_dataset_version_work, get_user_version_works,
    get_dataset_version_works, update_dataset_version_work, complete_dataset_version_work,
    cancel_dataset_version_work, delete_dataset_version_work, create_version_question,
    get_version_questions, update_version_question, delete_version_question,
    create_version_answer, update_version_answer, create_version_tag,
    get_version_work_statistics
)

router = APIRouter(prefix="/api/dataset-version-work", tags=["Dataset Version Work"])


# ============ Dataset Version Work Endpoints ============

@router.post("/", response_model=DatasetVersionWorkResponse)
def create_version_work(
    work_data: DatasetVersionWorkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建数据集版本工作"""
    try:
        work = create_dataset_version_work(db=db, work_data=work_data, user_id=current_user.id)
        return work
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{work_id}", response_model=DatasetVersionWorkResponse)
def get_version_work(
    work_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据集版本工作详情"""
    work = get_dataset_version_work(db=db, work_id=work_id)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version work not found"
        )
    
    # 检查权限（仅创建者或管理员可查看）
    if work.created_by != current_user.id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this version work"
        )
    
    return work


@router.get("/", response_model=List[DatasetVersionWorkSummary])
def get_my_version_works(
    skip: int = 0,
    limit: int = 20,
    status: Optional[WorkStatus] = None,
    dataset_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取我的版本工作列表"""
    works = get_user_version_works(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit,
        status=status,
        dataset_id=dataset_id
    )
    
    # 转换为概要格式并添加统计信息
    summaries = []
    for work in works:
        stats = get_version_work_statistics(db=db, work_id=work.id)
        summary = DatasetVersionWorkSummary(
            id=work.id,
            dataset_id=work.dataset_id,
            dataset_name=f"Dataset {work.dataset_id}",  # TODO: 从数据集表获取名称
            current_version=work.current_version,
            target_version=work.target_version,
            work_status=work.work_status,
            work_description=work.work_description,
            created_by=work.created_by,
            created_at=work.created_at,
            completed_at=work.completed_at,
            **stats
        )
        summaries.append(summary)
    
    return summaries


@router.get("/dataset/{dataset_id}", response_model=List[DatasetVersionWorkSummary])
def get_dataset_version_works_endpoint(
    dataset_id: int,
    skip: int = 0,
    limit: int = 20,
    status: Optional[WorkStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据集的版本工作列表"""
    works = get_dataset_version_works(
        db=db, 
        dataset_id=dataset_id, 
        skip=skip, 
        limit=limit,
        status=status
    )
    
    # 转换为概要格式
    summaries = []
    for work in works:
        stats = get_version_work_statistics(db=db, work_id=work.id)
        summary = DatasetVersionWorkSummary(
            id=work.id,
            dataset_id=work.dataset_id,
            dataset_name=f"Dataset {work.dataset_id}",  # TODO: 从数据集表获取名称
            current_version=work.current_version,
            target_version=work.target_version,
            work_status=work.work_status,
            work_description=work.work_description,
            created_by=work.created_by,
            created_at=work.created_at,
            completed_at=work.completed_at,
            **stats
        )
        summaries.append(summary)
    
    return summaries


@router.put("/{work_id}", response_model=DatasetVersionWorkResponse)
def update_version_work(
    work_id: int,
    work_update: DatasetVersionWorkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新数据集版本工作"""
    work = update_dataset_version_work(
        db=db, 
        work_id=work_id, 
        work_update=work_update,
        user_id=current_user.id
    )
    
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version work not found or no permission"
        )
    
    return work


@router.post("/{work_id}/complete", response_model=DatasetVersionWorkResponse)
def complete_version_work(
    work_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """完成数据集版本工作"""
    work = complete_dataset_version_work(db=db, work_id=work_id, user_id=current_user.id)
    
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version work not found, already completed, or no permission"
        )
    
    return work


@router.post("/{work_id}/cancel", response_model=DatasetVersionWorkResponse)
def cancel_version_work(
    work_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消数据集版本工作"""
    work = cancel_dataset_version_work(db=db, work_id=work_id, user_id=current_user.id)
    
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version work not found, already completed, or no permission"
        )
    
    return work


@router.delete("/{work_id}")
def delete_version_work(
    work_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除数据集版本工作"""
    success = delete_dataset_version_work(db=db, work_id=work_id, user_id=current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version work not found, already completed, or no permission"
        )
    
    return {"message": "Version work deleted successfully"}


# ============ Version Question Endpoints ============

@router.post("/{work_id}/questions", response_model=VersionStdQuestionResponse)
def create_question_in_version_work(
    work_id: int,
    question_data: VersionStdQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """在版本工作中创建问题"""
    # 验证版本工作存在且用户有权限
    work = get_dataset_version_work(db=db, work_id=work_id)
    if not work or work.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version work not found or no permission"
        )
    
    question = create_version_question(db=db, work_id=work_id, question_data=question_data)
    return question


@router.get("/{work_id}/questions", response_model=List[VersionStdQuestionResponse])
def get_questions_in_version_work(
    work_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取版本工作中的所有问题"""
    # 验证版本工作存在且用户有权限
    work = get_dataset_version_work(db=db, work_id=work_id)
    if not work or (work.created_by != current_user.id and current_user.role != 'admin'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version work not found or no permission"
        )
    
    questions = get_version_questions(db=db, work_id=work_id)
    return questions


@router.put("/questions/{question_id}", response_model=VersionStdQuestionResponse)
def update_question_in_version_work(
    question_id: int,
    question_update: VersionStdQuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新版本工作中的问题"""
    question = update_version_question(db=db, question_id=question_id, question_update=question_update)
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # 验证用户权限
    work = get_dataset_version_work(db=db, work_id=question.version_work_id)
    if not work or work.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to modify this question"
        )
    
    return question


@router.delete("/questions/{question_id}")
def delete_question_in_version_work(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除版本工作中的问题"""
    # TODO: 添加权限验证
    success = delete_version_question(db=db, question_id=question_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    return {"message": "Question deleted successfully"}


# ============ Version Answer Endpoints ============

@router.post("/{work_id}/answers", response_model=VersionStdAnswerResponse)
def create_answer_in_version_work(
    work_id: int,
    answer_data: VersionStdAnswerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """在版本工作中创建答案"""
    # 验证版本工作存在且用户有权限
    work = get_dataset_version_work(db=db, work_id=work_id)
    if not work or work.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version work not found or no permission"
        )
    
    answer = create_version_answer(db=db, work_id=work_id, answer_data=answer_data)
    return answer


@router.put("/answers/{answer_id}", response_model=VersionStdAnswerResponse)
def update_answer_in_version_work(
    answer_id: int,
    answer_update: VersionStdAnswerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新版本工作中的答案"""
    answer = update_version_answer(db=db, answer_id=answer_id, answer_update=answer_update)
    
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found"
        )
    
    # 验证用户权限
    work = get_dataset_version_work(db=db, work_id=answer.version_work_id)
    if not work or work.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to modify this answer"
        )
    
    return answer


# ============ Version Tag Endpoints ============

@router.post("/{work_id}/tags", response_model=VersionTagResponse)
def create_tag_in_version_work(
    work_id: int,
    tag_data: VersionTagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """在版本工作中创建标签"""
    # 验证版本工作存在且用户有权限
    work = get_dataset_version_work(db=db, work_id=work_id)
    if not work or work.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version work not found or no permission"
        )
    
    tag = create_version_tag(db=db, work_id=work_id, tag_data=tag_data)
    return tag


@router.post("/{work_id}/create-version", response_model=dict)
def create_new_version(
    work_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新版本 - 应用版本工作中的所有更改"""
    try:
        work = complete_dataset_version_work(db=db, work_id=work_id, user_id=current_user.id)
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version work not found, already completed, or no permission"
            )
        
        # 获取新创建的数据集版本信息
        from ..models.dataset import Dataset
        new_dataset = db.query(Dataset).filter(
            Dataset.id == work.dataset_id,
            Dataset.version == work.target_version
        ).first()
        
        # 统计新版本的内容
        from ..models.std_question import StdQuestion
        questions_count = db.query(StdQuestion).filter(
            StdQuestion.dataset_id == work.dataset_id,
            StdQuestion.current_version_id == work.target_version,
            StdQuestion.is_valid == True
        ).count()
        
        return {
            "success": True,
            "message": f"Successfully created version {work.target_version}",
            "version_info": {
                "dataset_id": work.dataset_id,
                "version": work.target_version,
                "questions_count": questions_count,
                "description": work.work_description,
                "created_at": work.completed_at.isoformat() if work.completed_at else None
            },
            "work": work
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create new version: {str(e)}"
        )


@router.post("/{work_id}/load-dataset")
def load_dataset_data(
    work_id: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """将现有数据集版本加载到版本工作中"""
    # 验证版本工作存在且用户有权限
    work = get_dataset_version_work(db=db, work_id=work_id)
    if not work or work.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version work not found or no permission"
        )
    
    dataset_id = request.get('dataset_id')
    version = request.get('version', 1)
    
    if not dataset_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="dataset_id is required"
        )
    
    try:
        from ..crud.crud_dataset_version_work import load_dataset_to_version_work
        success = load_dataset_to_version_work(db, work_id, dataset_id, version)
        
        if success:
            return {"success": True, "message": "Dataset loaded successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load dataset"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dataset: {str(e)}"
        )
