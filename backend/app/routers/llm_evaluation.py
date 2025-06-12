"""
LLM Evaluation Router for regular users
Provides marketplace access, task-based LLM evaluation, and result management
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from decimal import Decimal

from app.db.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.models.std_question import StdQuestion
from app.models.llm import LLM
from app.models.llm_answer import LLMAnswer
from app.models.llm_evaluation_task import LLMEvaluationTask, TaskStatus
from app.models.evaluation import Evaluation
from app.schemas.llm_evaluation_task import (
    LLMEvaluationTaskCreate, LLMEvaluationTaskResponse, LLMEvaluationTaskUpdate,
    LLMEvaluationTaskProgress, PromptTemplateInfo,
    EvaluationStartRequest, AvailableModel, EvaluationResultSummary,
    EvaluationDownloadRequest, ModelConfigRequest
)
from app.schemas.llm_answer import (
    MarketplaceDatasetInfo, DatasetDownloadResponse
)
from app.schemas.evaluation import EvaluationResponse
from app.crud.crud_llm_evaluation_task import (
    create_llm_evaluation_task, get_llm_evaluation_task, update_llm_evaluation_task,
    get_user_evaluation_tasks, get_task_progress
)
from app.crud.crud_llm import get_active_llms
from app.crud.crud_dataset import get_datasets_paginated
from app.services.llm_evaluation_service import LLMEvaluationTaskProcessor
from app.config.llm_config import get_default_system_prompt, get_default_evaluation_prompt

router = APIRouter(prefix="/api/llm-evaluation", tags=["LLM Evaluation"])

# 创建任务处理器实例
task_processor = LLMEvaluationTaskProcessor()


@router.get("/marketplace/datasets", response_model=List[MarketplaceDatasetInfo])
def get_marketplace_datasets(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据集市场列表（仅公开数据集）"""
    # 只显示公开的数据集
    datasets, total = get_datasets_paginated(
        db=db,
        skip=skip,
        limit=limit,
        is_public=True,
        search_query=search
    )
    
    marketplace_datasets = []
    for dataset in datasets:
        # 统计问题数量
        question_count = db.query(StdQuestion).filter(
            StdQuestion.current_dataset_id == dataset.id,
            StdQuestion.is_valid == True
        ).count()
        
        marketplace_datasets.append(MarketplaceDatasetInfo(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            version=dataset.version,
            question_count=question_count,
            is_public=dataset.is_public,
            created_by=dataset.created_by,
            create_time=dataset.create_time
        ))
    
    return marketplace_datasets


@router.get("/marketplace/datasets/{dataset_id}/download", response_model=DatasetDownloadResponse)
def download_dataset(
    dataset_id: int,
    format: str = "json",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载数据集（JSON格式）"""
    # 验证数据集存在且公开
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.is_public == True
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or not public"
        )
    
    # 获取数据集中的所有问题和答案
    questions = db.query(StdQuestion).filter(
        StdQuestion.current_dataset_id == dataset_id,
        StdQuestion.is_valid == True
    ).all()
    
    questions_data = []
    for question in questions:
        # 获取标准答案
        std_answers = [answer for answer in question.std_answers if answer.is_valid]
        answers_data = []
        
        for answer in std_answers:
            scoring_points = []
            for point in answer.scoring_points:
                scoring_points.append({
                    "answer": point.answer,
                    "point_order": point.point_order
                })
            
            answers_data.append({
                "id": answer.id,
                "answer": answer.answer,
                "scoring_points": scoring_points
            })
        
        questions_data.append({
            "id": question.id,
            "body": question.body,
            "question_type": question.question_type,
            "std_answers": answers_data
        })
    
    return DatasetDownloadResponse(
        dataset_info=MarketplaceDatasetInfo(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            version=dataset.version,
            question_count=len(questions_data),
            is_public=dataset.is_public,
            created_by=dataset.created_by,
            create_time=dataset.create_time
        ),
        questions=questions_data
    )


@router.get("/models", response_model=List[AvailableModel])
def get_available_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取可用的LLM模型列表"""
    # 从数据库获取活跃的模型
    db_models = get_active_llms(db)
    
    models = []
    for db_model in db_models:
        model = AvailableModel(
            id=db_model.name,  # 使用name作为id
            name=db_model.name,
            display_name=db_model.display_name,
            description=db_model.description or "",
            provider=db_model.provider,
            api_endpoint=db_model.api_endpoint or "",
            max_tokens=db_model.max_tokens or 4000,
            default_temperature=db_model.default_temperature or 0.7,
            top_k=db_model.top_k or 50,
            enable_reasoning=db_model.enable_reasoning or False,
            pricing={
                "input": float(db_model.cost_per_1k_tokens or 0.002),
                "output": float(db_model.cost_per_1k_tokens or 0.002) * 3  # 假设输出价格是输入的3倍
            }
        )
        models.append(model)
    
    return models


@router.get("/prompt-templates", response_model=List[PromptTemplateInfo])
def get_prompt_templates_list(
    template_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取基于llm_config的Prompt模板列表"""
    templates = []
    
    if template_type == "system" or template_type is None:
        # 系统模板
        templates.extend([
            PromptTemplateInfo(
                key="choice_system_default",
                name="选择题系统提示词",
                description="用于选择题的默认系统提示词",
                template_type="system",
                content=get_default_system_prompt("choice"),
                variables={}
            ),
            PromptTemplateInfo(
                key="text_system_default",
                name="文本题系统提示词", 
                description="用于文本题的默认系统提示词",
                template_type="system",
                content=get_default_system_prompt("text"),
                variables={}
            )
        ])
    
    if template_type == "evaluation" or template_type is None:
        # 评估模板
        templates.extend([
            PromptTemplateInfo(
                key="choice_evaluation_default",
                name="选择题评估提示词",
                description="用于选择题的默认评估提示词",
                template_type="evaluation",
                content=get_default_evaluation_prompt("choice"),
                variables={"question": "问题", "answer": "回答", "correct_answer": "正确答案"}
            ),
            PromptTemplateInfo(
                key="text_evaluation_default",
                name="文本题评估提示词",
                description="用于文本题的默认评估提示词", 
                template_type="evaluation",
                content=get_default_evaluation_prompt("text"),
                variables={"question": "问题", "answer": "回答", "correct_answer": "参考答案"}
            )
        ])
    
    return templates


@router.get("/prompt-templates/{template_key}", response_model=PromptTemplateInfo)
def get_prompt_template_by_key(
    template_key: str,
    current_user: User = Depends(get_current_user)
):
    """根据key获取指定的Prompt模板"""
    # 根据key返回对应的模板
    template_mapping = {
        "choice_system_default": PromptTemplateInfo(
            key="choice_system_default",
            name="选择题系统提示词",
            description="用于选择题的默认系统提示词",
            template_type="system",
            content=get_default_system_prompt("choice"),
            variables={}
        ),
        "text_system_default": PromptTemplateInfo(
            key="text_system_default", 
            name="文本题系统提示词",
            description="用于文本题的默认系统提示词",
            template_type="system",
            content=get_default_system_prompt("text"),
            variables={}
        ),
        "choice_evaluation_default": PromptTemplateInfo(
            key="choice_evaluation_default",
            name="选择题评估提示词",
            description="用于选择题的默认评估提示词",
            template_type="evaluation",
            content=get_default_evaluation_prompt("choice"),
            variables={"question": "问题", "answer": "回答", "correct_answer": "正确答案"}
        ),
        "text_evaluation_default": PromptTemplateInfo(
            key="text_evaluation_default",
            name="文本题评估提示词",
            description="用于文本题的默认评估提示词",
            template_type="evaluation", 
            content=get_default_evaluation_prompt("text"),
            variables={"question": "问题", "answer": "回答", "correct_answer": "参考答案"}
        )
    }
    
    template = template_mapping.get(template_key)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with key '{template_key}' not found"
        )
    
    return template


@router.post("/tasks", response_model=LLMEvaluationTaskResponse)
def create_evaluation_task(
    request: EvaluationStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建并启动LLM评测任务"""
    # 验证数据集存在
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    # 查找或创建LLM模型记录
    llm = db.query(LLM).filter(LLM.name == request.model_config.model_name).first()
    if not llm:
        llm = LLM(
            name=request.model_config.model_name,
            version=getattr(request.model_config, 'model_version', 'latest'),
            affiliation="API"
        )
        db.add(llm)
        db.commit()
        db.refresh(llm)    # 创建任务数据
    task_data = LLMEvaluationTaskCreate(
        name=request.task_name,
        description=f"LLM评测任务: {request.task_name}",
        dataset_id=request.dataset_id,
        model_id=llm.id,  # 使用LLM ID而不是名称
        system_prompt=request.model_config.system_prompt,
        temperature=getattr(request.model_config, 'temperature', Decimal("0.7")),
        max_tokens=getattr(request.model_config, 'max_tokens', 2000),
        top_k=getattr(request.model_config, 'top_k', 50),
        enable_reasoning=getattr(request.model_config, 'enable_reasoning', False),
        evaluation_llm_id=getattr(request.evaluation_config, 'evaluation_llm_id', None) if request.is_auto_score else None,
        evaluation_prompt=getattr(request.evaluation_config, 'evaluation_prompt', None) if request.is_auto_score else None,
        api_key=request.model_config.api_key
    )
    
    # 创建任务
    task = create_llm_evaluation_task(db=db, task_data=task_data, user_id=current_user.id)
    
    # 添加后台任务
    background_tasks.add_task(
        task_processor.process_evaluation_task,
        task.id,
        db,
        question_limit=request.question_limit
    )
    
    return LLMEvaluationTaskResponse.from_orm(task)


@router.get("/tasks", response_model=List[LLMEvaluationTaskResponse])
def get_my_evaluation_tasks(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取我的评测任务列表"""
    tasks = get_user_evaluation_tasks(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status_filter=status_filter
    )
    
    return [LLMEvaluationTaskResponse.from_orm(task) for task in tasks]


@router.get("/tasks/{task_id}", response_model=LLMEvaluationTaskResponse)
def get_evaluation_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取评测任务详情"""
    task = get_llm_evaluation_task(db=db, task_id=task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return LLMEvaluationTaskResponse.from_orm(task)


@router.get("/tasks/{task_id}/progress", response_model=LLMEvaluationTaskProgress)
def get_task_progress_endpoint(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务进度"""
    task = get_llm_evaluation_task(db=db, task_id=task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    progress_data = get_task_progress(db=db, task_id=task_id)
    
    return LLMEvaluationTaskProgress(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
        current_question=task.current_question,
        total_questions=task.total_questions,
        successful_count=task.successful_count,
        failed_count=task.failed_count,
        average_score=task.average_score,
        **progress_data
    )


@router.post("/tasks/{task_id}/cancel")
def cancel_evaluation_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消评测任务"""
    task = get_llm_evaluation_task(db=db, task_id=task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if task.status not in [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot be cancelled"
        )
    
    # 更新任务状态
    update_data = LLMEvaluationTaskUpdate(status="cancelled")
    update_llm_evaluation_task(db=db, task_id=task_id, task_update=update_data)
    
    return {"message": "Task cancelled successfully"}


@router.get("/tasks/{task_id}/results", response_model=EvaluationResultSummary)
def get_task_results(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取评测任务结果摘要"""
    task = get_llm_evaluation_task(db=db, task_id=task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if task.status != TaskStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task not completed yet"
        )
    
    return EvaluationResultSummary(
        task_id=task.id,
        task_name=task.task_name,
        dataset_name=task.dataset.name,
        model_name=task.model_name,
        total_questions=task.total_questions,
        successful_count=task.successful_count,
        failed_count=task.failed_count,
        average_score=task.average_score,
        completion_rate=task.successful_count / task.total_questions if task.total_questions > 0 else 0,
        created_at=task.created_at,
        completed_at=task.completed_at
    )


@router.post("/tasks/{task_id}/download")
def download_task_results(
    task_id: int,
    request: EvaluationDownloadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载评测结果"""
    task = get_llm_evaluation_task(db=db, task_id=task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # 获取任务的所有答案和评测结果
    answers = db.query(LLMAnswer).filter(
        LLMAnswer.evaluation_task_id == task_id
    ).all()
    
    results = []
    for answer in answers:
        answer_data = {
            "question_id": answer.std_question_id,
            "question_text": answer.std_question.body if answer.std_question else "",
            "llm_answer": answer.answer,
            "answered_at": answer.answered_at.isoformat() if answer.answered_at else None,
            "is_valid": answer.is_valid
        }
        
        if request.include_prompts and answer.prompt_used:
            answer_data["prompt_used"] = answer.prompt_used
        
        if request.include_raw_responses and answer.api_response:
            answer_data["api_response"] = answer.api_response
        
        # 添加评测结果
        evaluations = db.query(Evaluation).filter(
            Evaluation.llm_answer_id == answer.id
        ).all()
        
        answer_data["evaluations"] = []
        for eval in evaluations:
            answer_data["evaluations"].append({
                "score": eval.score,
                "evaluator_type": eval.evaluator_type.value,
                "feedback": eval.feedback,
                "evaluation_time": eval.evaluation_time.isoformat()
            })
        
        results.append(answer_data)
    
    return {
        "task_info": {
            "id": task.id,
            "name": task.task_name,
            "model": task.model_name,
            "dataset": task.dataset.name,
            "created_at": task.created_at.isoformat()
        },
        "results": results,
        "summary": {
            "total_questions": task.total_questions,
            "successful_count": task.successful_count,
            "failed_count": task.failed_count,
            "average_score": task.average_score
        }
    }
