from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.user import User
from app.models.expert_task import ExpertTask as ExpertTaskModel
from app.models.expert_answer import ExpertAnswer as ExpertAnswerModel
from app.models.raw_question import RawQuestion as RawQuestionModel
from app.auth import get_current_active_user
from app.schemas.expert_task import ExpertTask, ExpertTaskCreate, ExpertTaskUpdate, InviteCodeRequest
from app.schemas.raw_question import RawQuestion
from app.schemas.expert_answer import ExpertAnswerCreate, ExpertAnswer
from app.crud import crud_expert_task, crud_raw_question, crud_expert_answer
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/expert", tags=["expert"])

class ExpertDataImport(BaseModel):
    data: List[dict]

class DataImportResult(BaseModel):
    message: str
    imported_answers: int
    task_id: int

@router.post("/tasks", response_model=ExpertTask)
async def join_task_by_invite_code(
    invite_request: InviteCodeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """专家通过邀请码加入任务"""
    if current_user.role != "expert":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有专家用户可以加入任务"
        )
    
    try:
        task_data = ExpertTaskCreate(invite_code=invite_request.invite_code)
        task = crud_expert_task.create_expert_task(db, task_data, current_user.id)
        
        # 添加关联信息
        result = ExpertTask.from_orm(task)
        result.expert_username = task.expert.username
        result.admin_username = task.admin.username
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/tasks", response_model=List[ExpertTask])
async def get_my_tasks(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取专家的任务列表"""
    if current_user.role != "expert":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有专家用户可以查看任务"
        )
    
    tasks = crud_expert_task.get_expert_tasks(db, current_user.id, skip, limit)
    
    # 添加关联信息
    result = []
    for task in tasks:
        task_dict = ExpertTask.from_orm(task)
        task_dict.expert_username = task.expert.username
        task_dict.admin_username = task.admin.username
        result.append(task_dict)
    
    return result

@router.get("/tasks/{task_id}", response_model=ExpertTask)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取单个任务详情"""
    if current_user.role != "expert":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有专家用户可以查看任务"
        )
    
    task = crud_expert_task.get_expert_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    result = ExpertTask.from_orm(task)
    result.expert_username = task.expert.username
    result.admin_username = task.admin.username
    
    return result

@router.get("/tasks/{task_id}/questions", response_model=List[RawQuestion])
async def get_task_questions(
    task_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取任务对应的原始问题列表"""
    if current_user.role != "expert":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有专家用户可以查看问题"
        )
    
    # 验证任务是否属于当前专家
    task = crud_expert_task.get_expert_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 获取该管理员的原始问题
    result = crud_raw_question.get_raw_questions_paginated(
        db, skip=skip, limit=limit, 
        include_deleted=False, deleted_only=False, 
        created_by=task.admin_id
    )
    
    return result["data"]

@router.post("/answers", response_model=ExpertAnswer)
async def create_expert_answer(
    answer_data: ExpertAnswerCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """专家创建回答"""
    if current_user.role != "expert":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有专家用户可以创建回答"
        )
    
    # 验证专家是否有权限回答该问题（通过检查是否有对应的任务）
    question = crud_raw_question.get_raw_question(db, answer_data.question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="问题不存在"
        )
      # 检查专家是否有访问该问题的权限（通过任务）
    task = db.query(ExpertTaskModel).filter(
        ExpertTaskModel.expert_id == current_user.id,
        ExpertTaskModel.admin_id == question.created_by,
        ExpertTaskModel.is_active == True
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您没有权限回答该问题"
        )
    answer = crud_expert_answer.create_expert_answer(db, answer_data, current_user.id)
    return answer

@router.get("/answers", response_model=List[ExpertAnswer])
async def get_my_answers(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取专家的回答历史"""
    if current_user.role != "expert":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有专家用户可以查看回答历史"
        )
    
    answers = crud_expert_answer.get_expert_answers_by_author(db, current_user.id, skip, limit)
    return answers

@router.put("/tasks/{task_id}", response_model=ExpertTask)
async def update_task(
    task_id: int,
    task_update: ExpertTaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新任务信息"""
    if current_user.role != "expert":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有专家用户可以更新任务"
        )
    
    task = crud_expert_task.update_expert_task(db, task_id, current_user.id, task_update)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    result = ExpertTask.from_orm(task)
    result.expert_username = task.expert.username
    result.admin_username = task.admin.username
    
    return result

@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除任务"""
    if current_user.role != "expert":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有专家用户可以删除任务"
        )
    
    success = crud_expert_task.delete_expert_task(db, task_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return {"message": "任务已删除"}

@router.get("/invite-code/info")
async def get_invite_code_info(
    invite_code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """根据邀请码获取管理员信息"""
    if current_user.role != "expert":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有专家用户可以查看邀请码信息"
        )
    
    admin = crud_expert_task.get_admin_by_invite_code(db, invite_code)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无效的邀请码"
        )
    
    return {
        "admin_username": admin.username,
        "admin_id": admin.id,
        "invite_code": invite_code
    }

@router.post("/tasks/{task_id}/import-answers", response_model=DataImportResult)
async def import_expert_answers_to_task(
    task_id: int,
    import_data: ExpertDataImport,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """专家向特定任务导入回答数据"""
    if current_user.role != "expert":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有专家用户可以导入数据"
        )
      # 验证任务是否属于当前专家，并确保加载关联的管理员信息
    from sqlalchemy.orm import joinedload
    task = db.query(ExpertTaskModel).options(
        joinedload(ExpertTaskModel.admin)
    ).filter(
        ExpertTaskModel.id == task_id,
        ExpertTaskModel.expert_id == current_user.id,
        ExpertTaskModel.is_active == True
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在或您没有权限"
        )
    
    try:
        data = import_data.data
        imported_answers = 0
        
        for item in data:
            question_id = item.get('question_id')
            answer_text = item.get('answer')
            referenced_raw_answer_ids = item.get('referenced_raw_answer_ids', [])
            
            if not question_id or not answer_text:
                continue
                
            # 验证问题是否属于该任务的管理员
            question = db.query(RawQuestionModel).filter(
                RawQuestionModel.id == question_id,
                RawQuestionModel.created_by == task.admin_id
            ).first()
            
            if not question:
                continue  # 跳过不属于该管理员的问题
            
            # 检查是否已经存在该专家对该问题的回答
            existing_answer = db.query(ExpertAnswerModel).filter(
                ExpertAnswerModel.question_id == question_id,
                ExpertAnswerModel.answered_by == current_user.id,
                ExpertAnswerModel.is_deleted == False
            ).first()
            
            if existing_answer:
                # 更新现有回答
                existing_answer.answer = answer_text
                existing_answer.answered_at = datetime.now()
                # 注意：referenced_raw_answer_ids 在当前模型中可能需要额外处理
            else:                # 创建新回答
                expert_answer = ExpertAnswerModel(
                    question_id=question_id,
                    answer=answer_text,
                    answered_by=current_user.id,
                    answered_at=datetime.now(),
                    is_deleted=False
                )
                db.add(expert_answer)
                
            imported_answers += 1
        
        db.commit()
        
        # 获取管理员用户名用于返回消息
        try:
            admin_username = task.admin.username if hasattr(task, 'admin') and task.admin else f"管理员 {task.admin_id}"
        except Exception:
            admin_username = f"管理员 {task.admin_id}"
        
        return DataImportResult(
            message=f"成功导入 {imported_answers} 条专家回答到任务 {admin_username}",
            imported_answers=imported_answers,
            task_id=task_id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入数据时发生错误: {str(e)}"
        )
