"""
CRUD operations for LLM evaluation tasks
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func
from typing import List, Optional, Dict, Any
import hashlib
import logging
from datetime import datetime, timedelta, timezone

from ..models.llm_evaluation_task import LLMEvaluationTask, TaskStatus
from ..models.llm_answer import LLMAnswer
from ..models.dataset import Dataset
from ..models.std_question import StdQuestion
from ..schemas.llm_evaluation_task import (
    LLMEvaluationTaskCreate, LLMEvaluationTaskUpdate,
    ModelConfigRequest
)

logger = logging.getLogger(__name__)


def hash_api_key(api_key: str) -> str:
    """对API密钥进行哈希处理"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def create_llm_evaluation_task(
    db: Session, 
    task_data: LLMEvaluationTaskCreate, 
    user_id: int
) -> LLMEvaluationTask:
    """创建LLM评测任务"""
    # 获取数据集中的问题数
    total_questions = db.query(func.count(StdQuestion.id)).filter(
        StdQuestion.current_dataset_id == task_data.dataset_id,
        StdQuestion.is_valid == True
    ).scalar() or 0    
    # 处理API密钥 - 临时直接存储，实际应该使用可逆加密
    api_key_hash = None
    if task_data.api_key:
        # TODO: 使用可逆加密而不是直接存储
        api_key_hash = task_data.api_key  # 临时解决方案：直接存储
    
    # 创建任务
    task = LLMEvaluationTask(
        name=task_data.name,
        description=task_data.description,
        dataset_id=task_data.dataset_id,
        created_by=user_id,
        model_id=task_data.model_id,
        api_key_hash=api_key_hash,
        system_prompt=task_data.system_prompt,
        temperature=task_data.temperature,
        max_tokens=task_data.max_tokens,
        top_k=task_data.top_k,        
        enable_reasoning=task_data.enable_reasoning,
        evaluation_llm_id=task_data.evaluation_llm_id,
        evaluation_prompt=task_data.evaluation_prompt,
        status=TaskStatus.PENDING,
        total_questions=total_questions,
        progress=0,
        completed_questions=0,
        failed_questions=0    )
    
    logger.info(f"创建LLMEvaluationTask对象成功，准备添加到数据库")
    db.add(task)
    logger.info(f"已添加到session，准备commit")
    
    try:
        db.commit()
        logger.info(f"commit成功，准备refresh")
    except Exception as commit_error:
        logger.error(f"commit失败: {str(commit_error)}")
        import traceback
        logger.error(f"commit错误堆栈:\n{traceback.format_exc()}")
        raise
    
    try:
        db.refresh(task)
        logger.info(f"refresh成功，任务创建完成")
    except Exception as refresh_error:
        logger.error(f"refresh失败: {str(refresh_error)}")
        import traceback
        logger.error(f"refresh错误堆栈:\n{traceback.format_exc()}")
        raise
    return task


def get_llm_evaluation_task(db: Session, task_id: int) -> Optional[LLMEvaluationTask]:
    """获取LLM评测任务"""    
    return db.query(LLMEvaluationTask).options(
        joinedload(LLMEvaluationTask.dataset),
        joinedload(LLMEvaluationTask.user)
    ).filter(LLMEvaluationTask.id == task_id).first()


def get_user_evaluation_tasks(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 20,
    status: Optional[str] = None
) -> List[LLMEvaluationTask]:
    """获取用户的评测任务列"""
    query = db.query(LLMEvaluationTask).options(
        joinedload(LLMEvaluationTask.dataset)
    ).filter(LLMEvaluationTask.created_by == user_id)
    
    if status:
        query = query.filter(LLMEvaluationTask.status == status)
    
    return query.order_by(desc(LLMEvaluationTask.created_at)).offset(skip).limit(limit).all()


def get_dataset_evaluation_tasks(
    db: Session, 
    dataset_id: int, 
    user_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 10
) -> List[LLMEvaluationTask]:
    """获取数据集的评测任务"""
    query = db.query(LLMEvaluationTask).filter(
        LLMEvaluationTask.dataset_id == dataset_id
    )
    
    if user_id:
        query = query.filter(LLMEvaluationTask.created_by == user_id)
    
    return query.order_by(desc(LLMEvaluationTask.created_at)).offset(skip).limit(limit).all()


def update_llm_evaluation_task(
    db: Session, 
    task_id: int, 
    task_update: LLMEvaluationTaskUpdate
) -> Optional[LLMEvaluationTask]:
    """更新LLM评测任务"""
    logger.info(f"Task {task_id}: 开始update_llm_evaluation_task")
    
    try:
        task = db.query(LLMEvaluationTask).filter(LLMEvaluationTask.id == task_id).first()
        logger.info(f"Task {task_id}: 查询任务结果: {task is not None}")
        
        if not task:
            logger.error(f"Task {task_id}: 任务不存在")
            return None
        
        logger.info(f"Task {task_id}: 当前任务状态: {task.status}")
        
        update_data = task_update.model_dump(exclude_unset=True)
        logger.info(f"Task {task_id}: 准备更新的数据: {update_data}")
        for field, value in update_data.items():
            logger.info(f"Task {task_id}: 设置字段 {field} = {value}")
            setattr(task, field, value)
        
        # 自动设置时间戳
        logger.info(f"Task {task_id}: 检查时间戳设置")
        if task_update.status and task_update.status == TaskStatus.RUNNING and not task.started_at:
            logger.info(f"Task {task_id}: 设置started_at时间戳")
            task.started_at = datetime.now(timezone.utc)
        elif task_update.status and task_update.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and not task.completed_at:
            logger.info(f"Task {task_id}: 设置completed_at时间戳")
            task.completed_at = datetime.now(timezone.utc)
        
        logger.info(f"Task {task_id}: 准备执行db.commit()")
        db.commit()
        logger.info(f"Task {task_id}: db.commit()成功，准备执行db.refresh()")
        
        db.refresh(task)
        logger.info(f"Task {task_id}: db.refresh()成功，更新完成")
        return task
        
    except Exception as e:
        logger.error(f"Task {task_id}: update_llm_evaluation_task出错: {str(e)}")
        import traceback
        logger.error(f"Task {task_id}: update错误堆栈:\n{traceback.format_exc()}")
        db.rollback()
        raise


def delete_llm_evaluation_task(db: Session, task_id: int, user_id: int) -> bool:
    """删除LLM评测任务（仅任务创建者可删除）"""
    task = db.query(LLMEvaluationTask).filter(
        and_(
            LLMEvaluationTask.id == task_id,
            LLMEvaluationTask.created_by == user_id
        )
    ).first()
    
    if not task:
        return False
      # 只允许删除未开始或已完成的任务
      
    if task.status in [TaskStatus.PENDING.value, TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]:
        db.delete(task)
        db.commit()
        return True
    
    return False


def cancel_llm_evaluation_task(db: Session, task_id: int, user_id: int) -> Optional[LLMEvaluationTask]:
    """取消LLM评测任务"""
    task = db.query(LLMEvaluationTask).filter(
        and_(
            LLMEvaluationTask.id == task_id,
            LLMEvaluationTask.created_by == user_id,
            LLMEvaluationTask.status.in_([TaskStatus.PENDING.value, TaskStatus.RUNNING.value])
        )
    ).first()
    
    if not task:
        return None
    task.status = TaskStatus.CANCELLED
    task.completed_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(task)
    return task


def get_task_progress(db: Session, task_id: int) -> Dict[str, Any]:
    """获取任务进度信息"""
    task = db.query(LLMEvaluationTask).filter(LLMEvaluationTask.id == task_id).first()
    if not task:
        return {}
    
    # 计算预计剩余时间
    estimated_remaining_time = None
    questions_per_minute = None
    if task.status == TaskStatus.RUNNING and task.started_at:
        elapsed_time = (datetime.now() - task.started_at).total_seconds()
        if elapsed_time > 0 and task.completed_questions > 0:
            questions_per_minute = (task.completed_questions / elapsed_time) * 60
            remaining_questions = task.total_questions - task.completed_questions
            if questions_per_minute > 0:
                estimated_remaining_time = int(remaining_questions / questions_per_minute * 60)
    
    # 获取最新答案和评分
    latest_answer = None
    latest_score = None
    if task.llm_answers:
        latest_llm_answer = sorted(task.llm_answers, key=lambda x: x.answered_at, reverse=True)[0]
        latest_answer = latest_llm_answer.answer[:100] + "..." if len(latest_llm_answer.answer) > 100 else latest_llm_answer.answer
        
        # 获取最新评分
        if latest_llm_answer.evaluations:
            latest_evaluation = sorted(latest_llm_answer.evaluations, key=lambda x: x.evaluation_time, reverse=True)[0]
            latest_score = latest_evaluation.score
    
    return {
        "estimated_remaining_time": estimated_remaining_time,
        "questions_per_minute": questions_per_minute,
        "latest_answer": latest_answer,
        "latest_score": latest_score
    }
