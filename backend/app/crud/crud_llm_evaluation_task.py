"""
CRUD operations for LLM evaluation tasks
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func
from typing import List, Optional, Dict, Any
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from ..models.llm_evaluation_task import LLMEvaluationTask, TaskStatus
from ..models.llm_answer import LLMAnswer
from ..models.dataset import Dataset
from ..models.std_question import StdQuestion
from ..models.evaluation import Evaluation
from ..schemas.llm_evaluation_task import (
    LLMEvaluationTaskCreate, LLMEvaluationTaskUpdate,
    ModelConfigRequest, ManualEvaluationTaskCreate
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
    # 获取数据集的所有标准问题，使用复合主键
    std_questions = db.query(StdQuestion).filter(
        StdQuestion.dataset_id == task_data.dataset_id,
        StdQuestion.current_version_id == task_data.dataset_version,  # 使用dataset_version
        StdQuestion.is_valid == True
    ).all()
    total_questions = len(std_questions)
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
        dataset_version=task_data.dataset_version,  # 添加dataset_version字段
        created_by=user_id,
        model_id=task_data.model_id,
        api_key_hash=api_key_hash,
        system_prompt=task_data.system_prompt,
        choice_system_prompt=task_data.choice_system_prompt,
        text_system_prompt=task_data.text_system_prompt,
        choice_evaluation_prompt=task_data.choice_evaluation_prompt,
        text_evaluation_prompt=task_data.text_evaluation_prompt,
        temperature=task_data.temperature,
        max_tokens=task_data.max_tokens,
        top_k=task_data.top_k,        
        enable_reasoning=task_data.enable_reasoning,
        evaluation_prompt=task_data.evaluation_prompt,
        status=TaskStatus.CONFIG_PARAMS,
        total_questions=total_questions,
        progress=0,
        completed_questions=0,
        failed_questions=0
    )
    
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
        joinedload(LLMEvaluationTask.model),
        joinedload(LLMEvaluationTask.user)
    ).filter(LLMEvaluationTask.id == task_id).first()


def get_user_evaluation_tasks(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 20,
    status: Optional[str] = None
) -> List[LLMEvaluationTask]:
    """获取用户的评测任务列表"""
    query = db.query(LLMEvaluationTask).options(
        joinedload(LLMEvaluationTask.dataset),
        joinedload(LLMEvaluationTask.model),
    ).filter(LLMEvaluationTask.created_by == user_id)
    
    if status:
        query = query.filter(LLMEvaluationTask.status == status)
    
    return query.order_by(desc(LLMEvaluationTask.created_at)).offset(skip).limit(limit).all()


def get_dataset_evaluation_tasks(
    db: Session, 
    dataset_id: int, 
    dataset_version: Optional[int] = None,
    user_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 10
) -> List[LLMEvaluationTask]:
    """获取数据集的评测任务"""
    query = db.query(LLMEvaluationTask).filter(
        LLMEvaluationTask.dataset_id == dataset_id
    )
    
    # 如果指定了版本，则过滤版本
    if dataset_version is not None:
        query = query.filter(LLMEvaluationTask.dataset_version == dataset_version)
    
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
        if task_update.status and task_update.status == TaskStatus.GENERATING_ANSWERS and not task.started_at:
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
      
    if task.status in [TaskStatus.CONFIG_PARAMS.value, TaskStatus.CONFIG_PROMPTS.value, TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]:
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
            LLMEvaluationTask.status.in_([TaskStatus.CONFIG_PARAMS.value, TaskStatus.CONFIG_PROMPTS.value, TaskStatus.GENERATING_ANSWERS.value, TaskStatus.EVALUATING_ANSWERS.value])
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
    if task.status in [TaskStatus.GENERATING_ANSWERS, TaskStatus.EVALUATING_ANSWERS] and task.started_at:
        elapsed_time = (datetime.now() - task.started_at).total_seconds()
        if elapsed_time > 0 and task.completed_questions > 0:
            questions_per_minute = (task.completed_questions / elapsed_time) * 60
            remaining_questions = task.total_questions - task.completed_questions
            if questions_per_minute > 0:
                estimated_remaining_time = int(remaining_questions / questions_per_minute * 60)
    
    # 根据任务状态返回不同的进度信息
    latest_content = None
    latest_score = None
    latest_content_type = "answer"  # "answer" 或 "evaluation"
    
    if task.status == TaskStatus.GENERATING_ANSWERS:
        # 答案生成阶段：显示最新生成的答案
        if task.llm_answers:
            latest_llm_answer = sorted(task.llm_answers, key=lambda x: x.answered_at, reverse=True)[0]
            latest_content = latest_llm_answer.answer[:200] + "..." if len(latest_llm_answer.answer) > 200 else latest_llm_answer.answer
            latest_content_type = "answer"
            
    elif task.status == TaskStatus.EVALUATING_ANSWERS:
        # 评测阶段：显示最新的评测结果
        if task.llm_answers:
            # 查找最新有评测的答案
            answers_with_evaluations = []
            for answer in task.llm_answers:
                if answer.evaluations:
                    latest_eval = sorted(answer.evaluations, key=lambda x: x.evaluation_time, reverse=True)[0]
                    answers_with_evaluations.append((answer, latest_eval))
            
            if answers_with_evaluations:
                # 按评测时间排序，获取最新的评测
                latest_answer, latest_evaluation = sorted(answers_with_evaluations, 
                                                        key=lambda x: x[1].evaluation_time, reverse=True)[0]
                latest_content = f"评分: {latest_evaluation.score}/100\n评测内容: {latest_evaluation.reasoning[:150]}..." if latest_evaluation.reasoning and len(latest_evaluation.reasoning) > 150 else f"评分: {latest_evaluation.score}/100\n评测内容: {latest_evaluation.reasoning or '无评测理由'}"
                latest_score = latest_evaluation.score
                latest_content_type = "evaluation"
            else:
                # 如果还没有评测结果，显示最新答案
                latest_llm_answer = sorted(task.llm_answers, key=lambda x: x.answered_at, reverse=True)[0]
                latest_content = latest_llm_answer.answer[:200] + "..." if len(latest_llm_answer.answer) > 200 else latest_llm_answer.answer
                latest_content_type = "answer"
    else:
        # 其他状态：显示最新答案和评分
        if task.llm_answers:
            latest_llm_answer = sorted(task.llm_answers, key=lambda x: x.answered_at, reverse=True)[0]
            latest_content = latest_llm_answer.answer[:200] + "..." if len(latest_llm_answer.answer) > 200 else latest_llm_answer.answer
            
            # 获取最新评分
            if latest_llm_answer.evaluations:
                latest_evaluation = sorted(latest_llm_answer.evaluations, key=lambda x: x.evaluation_time, reverse=True)[0]
                latest_score = latest_evaluation.score
    
    return {
        "estimated_remaining_time": estimated_remaining_time,
        "questions_per_minute": questions_per_minute,
        "latest_content": latest_content,
        "latest_score": latest_score,
        "latest_content_type": latest_content_type,
    }


def create_manual_evaluation_task(
    db: Session,
    task_data: ManualEvaluationTaskCreate,
    user_id: int
) -> LLMEvaluationTask:
    """创建手动录入的评测任务"""
    from ..models.llm_answer import LLMAnswer
    from ..models.evaluation import Evaluation, EvaluatorType
    from ..models.std_question import StdQuestion
    
    try:        # 验证所有问题ID是否有效
        question_ids = [entry.question_id for entry in task_data.entries]
        valid_questions = db.query(StdQuestion).filter(
            StdQuestion.id.in_(question_ids),
            StdQuestion.dataset_id == task_data.dataset_id,
            StdQuestion.current_version_id == task_data.dataset_version,  # 添加版本检查
            StdQuestion.is_valid == True
        ).all()
        
        if len(valid_questions) != len(question_ids):
            raise ValueError("部分问题ID无效或不属于指定数据集版本")
        
        # 计算平均分
        total_score = sum(entry.score for entry in task_data.entries)
        avg_score = total_score / len(task_data.entries) if task_data.entries else 0
        
        # 创建评测任务（直接设置为已完成状态）
        task = LLMEvaluationTask(
            name=task_data.name,
            description=task_data.description,
            dataset_id=task_data.dataset_id,
            dataset_version=task_data.dataset_version,  # 添加dataset_version字段
            created_by=user_id,
            model_id=task_data.model_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            score=avg_score,
            total_questions=len(task_data.entries),
            completed_questions=len(task_data.entries),
            failed_questions=0,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            # 高级配置选项
            system_prompt=task_data.system_prompt,
            choice_system_prompt=task_data.choice_system_prompt,
            text_system_prompt=task_data.text_system_prompt,
            choice_evaluation_prompt=task_data.choice_evaluation_prompt,
            text_evaluation_prompt=task_data.text_evaluation_prompt,
            evaluation_prompt=task_data.evaluation_prompt,
            temperature=Decimal(str(task_data.temperature)) if task_data.temperature else Decimal("0.7"),
            max_tokens=task_data.max_tokens or 2000,
            top_k=task_data.top_k or 50,
            enable_reasoning=task_data.enable_reasoning or False
        )
        
        db.add(task)
        db.flush()
        
        # 创建LLM答案和评测记录
        for entry in task_data.entries:
            # 创建LLM答案记录
            llm_answer = LLMAnswer(
                task_id=task.id,
                std_question_id=entry.question_id,  # 修正字段名
                answer=entry.answer,
                is_valid=True,
                answered_at=datetime.now()
            )
            db.add(llm_answer)
            db.flush()  # 获取答案ID
            
            # 创建评测记录
            evaluation = Evaluation(
                std_question_id=entry.question_id,
                llm_answer_id=llm_answer.id,
                score=entry.score,
                evaluator_type=EvaluatorType.USER,  # 用户手动评测
                evaluator_id=user_id,
                reasoning=entry.reasoning or "手动录入",
                evaluation_prompt="手动录入评测结果"
            )
            db.add(evaluation)
        
        # 生成结果摘要
        result_summary = {
            "total_questions": len(task_data.entries),
            "completed_questions": len(task_data.entries),
            "failed_questions": 0,
            "average_score": avg_score,
            "score_distribution": _calculate_score_distribution([entry.score for entry in task_data.entries]),
            "evaluation_type": "manual",
            "created_at": datetime.now().isoformat()
        }
        task.result_summary = result_summary
        
        db.commit()
        logger.info(f"Manual evaluation task created successfully: {task.id}")
        return task
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating manual evaluation task: {str(e)}")
        raise


def _calculate_score_distribution(scores: List[float]) -> Dict[str, int]:
    """计算分数分布"""
    distribution = {
        "excellent": 0,  # 90-100
        "good": 0,       # 70-89
        "fair": 0,       # 50-69
        "poor": 0        # 0-49
    }
    
    for score in scores:
        if score >= 90:
            distribution["excellent"] += 1
        elif score >= 70:
            distribution["good"] += 1
        elif score >= 50:
            distribution["fair"] += 1
        else:
            distribution["poor"] += 1
    
    return distribution


def calculate_and_update_task_score(db: Session, task_id: int) -> Optional[float]:
    """计算并更新任务的总体得分（所有evaluation的平均分）"""
    from decimal import Decimal
    
    logger.info(f"Task {task_id}: 开始计算任务总分")
    
    try:
        # 获取任务
        task = db.query(LLMEvaluationTask).filter(LLMEvaluationTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id}: 任务不存在")
            return None
        
        # 获取所有evaluation结果
        llm_answers = db.query(LLMAnswer).filter(LLMAnswer.task_id == task_id).all()
        
        total_score = 0
        valid_scores = 0
        
        for answer in llm_answers:
            evaluations = db.query(Evaluation).filter(
                Evaluation.llm_answer_id == answer.id,
                Evaluation.score.isnot(None)
            ).all()
            
            # 计算该答案的平均分
            answer_scores = [float(e.score) for e in evaluations if e.score is not None]
            if answer_scores:
                avg_score = sum(answer_scores) / len(answer_scores)
                total_score += avg_score
                valid_scores += 1
        
        # 计算总体平均分
        overall_average = total_score / valid_scores if valid_scores > 0 else 0
        
        # 更新任务得分
        task.score = Decimal(str(round(overall_average, 2)))
        db.commit()
        db.refresh(task)
        
        logger.info(f"Task {task_id}: 总分计算完成，得分: {overall_average}")
        return overall_average
        
    except Exception as e:
        logger.error(f"Task {task_id}: 计算总分时出错: {str(e)}")
        db.rollback()
        return None


def update_task_when_evaluation_completed(db: Session, task_id: int):
    """当评测完成时更新任务状态和得分"""
    logger.info(f"Task {task_id}: 检查是否需要更新任务状态")
    
    try:
        # 检查是否所有答案都已评测完成
        total_answers = db.query(LLMAnswer).filter(LLMAnswer.task_id == task_id).count()
        
        evaluated_answers = db.query(LLMAnswer).join(Evaluation).filter(
            LLMAnswer.task_id == task_id,
            Evaluation.score.isnot(None)
        ).distinct().count()
        
        logger.info(f"Task {task_id}: 总答案数: {total_answers}, 已评测数: {evaluated_answers}")
        
        if total_answers > 0 and evaluated_answers >= total_answers:
            # 所有答案都已评测，计算总分并更新状态
            calculate_and_update_task_score(db, task_id)
            
            # 更新任务状态为完成
            task = db.query(LLMEvaluationTask).filter(LLMEvaluationTask.id == task_id).first()
            if task and task.status != TaskStatus.COMPLETED:
                task.status = TaskStatus.COMPLETED
                task.progress = 100
                task.completed_at = datetime.now(timezone.utc)
                db.commit()
                logger.info(f"Task {task_id}: 任务状态已更新为COMPLETED")
                
    except Exception as e:
        logger.error(f"Task {task_id}: 更新任务状态时出错: {str(e)}")
        db.rollback()
