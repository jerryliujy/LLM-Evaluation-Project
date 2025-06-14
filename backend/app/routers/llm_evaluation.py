"""
LLM Evaluation Router for regular users
Provides marketplace access, task-based LLM evaluation, and result management
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime
from decimal import Decimal

from app.db.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.models.std_question import StdQuestion
from app.models.std_answer import StdAnswer
from app.models.llm import LLM
from app.models.llm_answer import LLMAnswer
from app.models.llm_evaluation_task import LLMEvaluationTask, TaskStatus
from app.models.evaluation import Evaluation
from app.schemas.llm_evaluation_task import (
    LLMEvaluationTaskCreate, LLMEvaluationTaskResponse, LLMEvaluationTaskUpdate,
    LLMEvaluationTaskProgress, PromptTemplateInfo,
    EvaluationStartRequest, AvailableModel, EvaluationResultSummary,
    EvaluationDownloadRequest, ModelConfigRequest,
    ManualEvaluationTaskCreate, ManualEvaluationTaskResponse
)
from app.schemas.llm_answer import (
    MarketplaceDatasetInfo, DatasetDownloadResponse
)
from app.schemas.evaluation import EvaluationResponse
from app.crud.crud_llm_evaluation_task import (
    create_llm_evaluation_task, get_llm_evaluation_task, update_llm_evaluation_task,
    get_user_evaluation_tasks, get_task_progress, create_manual_evaluation_task
)
from app.crud.crud_llm import get_active_llms
from app.crud.crud_dataset import get_datasets_paginated
from app.services.llm_evaluation_service import LLMEvaluationTaskProcessor
from app.config.llm_config import get_default_system_prompt, get_default_evaluation_prompt

router = APIRouter(prefix="/api/llm-evaluation", tags=["LLM Evaluation"])

# 创建logger实例
logger = logging.getLogger(__name__)

# 创建任务处理器实例
task_processor = LLMEvaluationTaskProcessor()


@router.get("/marketplace/datasets", response_model=List[MarketplaceDatasetInfo])
def get_marketplace_datasets(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    all_datasets: bool = False,  # 新增：是否获取所有数据集
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取公开数据集市场列表"""    # 根据参数决定是否限制数量
    actual_limit = None if all_datasets else limit
    
    datasets, total_count = get_datasets_paginated(
        db=db, 
        skip=skip, 
        limit=actual_limit,
        is_public=True,
        search_query=search,
    )
    
    marketplace_datasets = []
    for dataset in datasets:
        # 统计问题总数
        question_count = db.query(StdQuestion).filter(
            StdQuestion.dataset_id == dataset.id,
            StdQuestion.is_valid == True
        ).count()
        
        # 统计选择题数量
        choice_question_count = db.query(StdQuestion).filter(
            StdQuestion.dataset_id == dataset.id,
            StdQuestion.is_valid == True,
            StdQuestion.question_type == 'choice'
        ).count()
        
        # 统计文本题数量
        text_question_count = db.query(StdQuestion).filter(
            StdQuestion.dataset_id == dataset.id,
            StdQuestion.is_valid == True,
            StdQuestion.question_type == 'text'
        ).count()
        
        marketplace_datasets.append(MarketplaceDatasetInfo(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            version=dataset.version,
            question_count=question_count,
            choice_question_count=choice_question_count,
            text_question_count=text_question_count,
            is_public=dataset.is_public,
            created_by=dataset.created_by,
            create_time=dataset.create_time
        ))
    
    return marketplace_datasets


@router.get("/marketplace/datasets/{dataset_id}", response_model=MarketplaceDatasetInfo)
def get_marketplace_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个数据集的详细信息（仅公开数据集）"""
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
    
    # 获取数据集的所有标准问题
    std_questions = db.query(StdQuestion).filter(
        StdQuestion.dataset_id == dataset.id,  # 使用dataset_id而不是current_dataset_id
        StdQuestion.is_valid == True
    ).all()
    
    # 统计问题总数
    question_count = len(std_questions)
    
    # 统计选择题数量
    choice_question_count = len([q for q in std_questions if q.question_type == 'choice'])
    
    # 统计文本题数量
    text_question_count = len([q for q in std_questions if q.question_type == 'text'])
    
    return MarketplaceDatasetInfo(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        version=dataset.version,
        question_count=question_count,
        choice_question_count=choice_question_count,
        text_question_count=text_question_count,
        is_public=dataset.is_public,
        created_by=dataset.created_by,
        create_time=dataset.create_time
    )


@router.get("/marketplace/datasets/{dataset_id}/download", response_model=DatasetDownloadResponse)
def download_marketplace_dataset(
    dataset_id: int,
    format: str = "json",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载数据集的问题数据"""
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
    
    # 获取数据集的所有标准问题
    std_questions = db.query(StdQuestion).filter(
        StdQuestion.dataset_id == dataset.id,  # 使用dataset_id而不是current_dataset_id
        StdQuestion.is_valid == True
    ).all()
    
    # 获取数据集的基本信息
    question_count = len(std_questions)
    
    choice_question_count = len([q for q in std_questions if q.question_type == 'choice'])
    
    text_question_count = len([q for q in std_questions if q.question_type == 'text'])
    
    dataset_info = MarketplaceDatasetInfo(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        version=dataset.version,
        question_count=question_count,
        choice_question_count=choice_question_count,
        text_question_count=text_question_count,
        is_public=dataset.is_public,
        created_by=dataset.created_by,
        create_time=dataset.create_time
    )
    
    # 获取数据集的问题
    questions = std_questions[:100]  # 限制数量以防止过大的响应
    
    # 转换为响应格式
    question_data = []
    for question in questions:
        question_info = {
            "id": question.id,
            "question": question.question,
            "question_type": question.question_type,
            "difficulty": question.difficulty,
            "tags": question.tags,
            "std_answer": question.std_answer,
            "choices": question.choices
        }
        question_data.append(question_info)
    
    return DatasetDownloadResponse(
        dataset_info=dataset_info,
        questions=question_data
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
            id=db_model.id, 
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
            detail="Template not found"
        )
    
    return template


@router.post("/tasks", response_model=LLMEvaluationTaskResponse)
async def create_evaluation_task(
    request: EvaluationStartRequest,
    raw_request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建并启动LLM评测任务"""
    try:
        # 获取原始请求体
        body = await raw_request.body()
        print(f"=== Raw Request Body ===")
        print(f"Body: {body.decode('utf-8')}")
        print(f"Body parsed: {json.loads(body.decode('utf-8'))}")
        print(f"========================")
        
        # 打印调试信息
        print(f"=== Debug Info ===")
        print(f"Request type: {type(request)}")
        print(f"Request data: {request}")
        print(f"Request dict: {request.dict()}")        
        print(f"Model config: {request.model_settings}")
        print(f"Model config type: {type(request.model_settings)}")
        if hasattr(request.model_settings, '__dict__'):
            print(f"Model config dict: {request.model_settings.__dict__}")
        if hasattr(request.model_settings, 'model_id'):
            print(f"Model config model_id: {request.model_settings.model_id}")
        print(f"=================")
    except Exception as e:
        print(f"Error in debug info: {e}")
        import traceback
        traceback.print_exc()

    # 验证数据集存在
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # 直接通过model_id查找LLM模型记录
    model_id = request.model_settings.model_id if hasattr(request.model_settings, 'model_id') else request.model_settings.get('model_id')
    print(f"Extracted model_id: {model_id}")
    
    if not model_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model ID is required"
        )
    
    llm = db.query(LLM).filter(LLM.id == model_id).first()
    if not llm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )    # 创建任务数据
    def get_config_value(config, key, default=None):
        """从配置对象中获取值，支持Pydantic模型和字典"""
        if hasattr(config, key):
            return getattr(config, key, default)
        elif hasattr(config, 'get'):
            return config.get(key, default)
        else:
            return default
        
    task_data = LLMEvaluationTaskCreate(
        name=request.task_name,
        description=f"LLM评测任务: {request.task_name}",
        dataset_id=request.dataset_id,
        model_id=llm.id,  # 使用验证过的LLM ID
        system_prompt=get_config_value(request.model_settings, 'system_prompt'),
        choice_system_prompt=get_config_value(request.model_settings, 'choice_system_prompt'),
        text_system_prompt=get_config_value(request.model_settings, 'text_system_prompt'),        choice_evaluation_prompt=get_config_value(request.evaluation_config, 'choice_evaluation_prompt') if request.evaluation_config else None,
        text_evaluation_prompt=get_config_value(request.evaluation_config, 'text_evaluation_prompt') if request.evaluation_config else None,
        temperature=Decimal(str(get_config_value(request.model_settings, 'temperature', 0.7))),  # 转换为Decimal
        max_tokens=get_config_value(request.model_settings, 'max_tokens', 2000),
        top_k=get_config_value(request.model_settings, 'top_k', 50),
        enable_reasoning=get_config_value(request.model_settings, 'enable_reasoning', False),
        evaluation_prompt=get_config_value(request.evaluation_config, 'evaluation_prompt') if request.evaluation_config else None,
        api_key=get_config_value(request.model_settings, 'api_key')
    )
    
    # 创建任务
    logger.info(f"开始创建LLM评测任务: {request.task_name}")
    try:
        task = create_llm_evaluation_task(db=db, task_data=task_data, user_id=current_user.id)
        logger.info(f"任务创建成功，任务ID: {task.id}")
    except Exception as create_error:
        logger.error(f"创建任务失败: {str(create_error)}")
        import traceback
        logger.error(f"创建任务错误堆栈:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(create_error)}")
    
    # 添加后台任务
    logger.info(f"开始添加后台任务，任务ID: {task.id}")
    try:
        background_tasks.add_task(
            task_processor.process_evaluation_task,
            task.id,
            request.question_limit
        )
        logger.info(f"后台任务添加成功，任务ID: {task.id}")
    except Exception as bg_error:
        logger.error(f"添加后台任务失败: {str(bg_error)}")
        import traceback
        logger.error(f"后台任务错误堆栈:\n{traceback.format_exc()}")
        # 即使后台任务失败，也要返回任务，但状态会是FAILED
    
    return LLMEvaluationTaskResponse.from_orm(task)


@router.post("/tasks/manual", response_model=ManualEvaluationTaskResponse)
def create_manual_evaluation_task_endpoint(
    task_data: ManualEvaluationTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建手动录入的评测任务"""
    try:
        logger.info(f"User {current_user.id} creating manual evaluation task: {task_data.name}")
        
        # 验证数据集是否存在且用户有权限访问
        dataset = db.query(Dataset).filter(Dataset.id == task_data.dataset_id).first()
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # 验证数据集是否公开或用户有权限
        if not dataset.is_public and dataset.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to access this dataset"
            )
        
        # 验证LLM模型是否存在
        llm_model = db.query(LLM).filter(LLM.id == task_data.model_id).first()
        if not llm_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM model not found"
            )
        
        # 验证评测条目不为空
        if not task_data.entries:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Evaluation entries cannot be empty"
            )
        
        # 创建手动评测任务
        task = create_manual_evaluation_task(
            db=db,
            task_data=task_data,
            user_id=current_user.id
        )
        
        logger.info(f"Manual evaluation task created successfully: {task.id}")
        
        # 返回任务信息
        return ManualEvaluationTaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            dataset={
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description
            },
            model={
                "id": llm_model.id,
                "name": llm_model.name,
                "display_name": llm_model.display_name or llm_model.name,
                "version": llm_model.version
            },
            status=task.status,
            score=float(task.score) if task.score else None,
            total_questions=task.total_questions,
            completed_questions=task.completed_questions,
            created_at=task.created_at,
            completed_at=task.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating manual evaluation task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create manual evaluation task: {str(e)}"
        )


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
        status=status_filter
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
    
    if task.created_by != current_user.id:
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
    
    if task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    progress_data = get_task_progress(db=db, task_id=task_id)
    return LLMEvaluationTaskProgress(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
        total_questions=task.total_questions,
        completed_questions=task.completed_questions,
        failed_questions=task.failed_questions,
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
    
    if task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if task.status not in [TaskStatus.CONFIG_PARAMS.value, TaskStatus.CONFIG_PROMPTS.value, TaskStatus.GENERATING_ANSWERS.value, TaskStatus.EVALUATING_ANSWERS.value]:
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
    
    if task.created_by != current_user.id:
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
        task_name=task.name,  # 使用name字段
        dataset_name=task.dataset.name,
        model_name=task.model.name if task.model else "Unknown",  # 使用关联的模型名称
        total_questions=task.total_questions,
        successful_count=task.completed_questions,  # 使用completed_questions
        failed_count=task.failed_questions,
        average_score=task.score,  # 使用score字段
        completion_rate=task.completed_questions / task.total_questions if task.total_questions > 0 else 0,
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
    
    if task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # 获取任务的所有答案和评测结果
    answers = db.query(LLMAnswer).filter(
        LLMAnswer.task_id == task_id
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
        
        # 添加评测结果
        evaluations = db.query(Evaluation).filter(
            Evaluation.llm_answer_id == answer.id
        ).all()
        
        answer_data["evaluations"] = []
        for eval in evaluations:
            answer_data["evaluations"].append({
                "score": eval.score,
                "evaluator_type": eval.evaluator_type.value,
                "evaluation_time": eval.evaluation_time.isoformat()
            })
        
        results.append(answer_data)
    
    return {
        "task_info": {
            "id": task.id,
            "name": task.name,  # 使用name字段
            "model": task.model.name if task.model else "Unknown",  # 使用关联的模型名称
            "dataset": task.dataset.name,
            "created_at": task.created_at.isoformat()
        },
        "results": results,
        "summary": {
            "total_questions": task.total_questions,
            "successful_count": task.completed_questions,  # 使用completed_questions
            "failed_count": task.failed_questions,
            "average_score": task.score  # 使用score字段
        }
    }


@router.put("/tasks/{task_id}/status", response_model=LLMEvaluationTaskResponse)
def update_task_status(
    task_id: int,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新任务状态 - 支持阶段性推进"""
    # 获取任务
    task = get_llm_evaluation_task(db=db, task_id=task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 验证用户权限
    if task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    new_status = status_update.get('status')
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status is required"
        )    # 验证状态转换的合法性
    valid_transitions = {
        'config_params': ['config_prompts', 'cancelled'],
        'config_prompts': ['generating_answers', 'cancelled'],
        'generating_answers': ['evaluating_answers', 'failed', 'cancelled'],
        'evaluating_answers': ['completed', 'failed', 'cancelled']
    }
    
    current_status = task.status.value if hasattr(task.status, 'value') else task.status
    if current_status in valid_transitions:
        if new_status not in valid_transitions[current_status]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {current_status} to {new_status}"
            )
    
    # 更新任务状态
    update_data = LLMEvaluationTaskUpdate(
        status=new_status,
        **{k: v for k, v in status_update.items() if k != 'status'}
    )
    
    updated_task = update_llm_evaluation_task(db=db, task_id=task_id, task_update=update_data)
    
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task"
        )
    
    return updated_task


@router.post("/tasks/{task_id}/start-evaluation")
def start_task_evaluation(
    task_id: int,
    evaluation_config: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """启动评测阶段 - 对已生成的LLM答案进行评测"""
    # 获取任务
    task = get_llm_evaluation_task(db=db, task_id=task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 验证用户权限
    if task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
      # 验证任务状态 - 只有evaluating_answers状态的任务可以启动评测
    if task.status != TaskStatus.EVALUATING_ANSWERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start evaluation for task in status: {task.status.value}. Task must be in 'evaluating_answers' status."
        )
    
    # 检查是否有LLM答案需要评测
    answers = db.query(LLMAnswer).filter(LLMAnswer.task_id == task_id).all()
    if not answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No LLM answers found for this task"
        )
    try:
        # 更新评测配置（如果提供了新的评测prompt）
        if evaluation_config.get('evaluation_prompt'):
            update_data = LLMEvaluationTaskUpdate(
                evaluation_prompt=evaluation_config.get('evaluation_prompt')
            )
            updated_task = update_llm_evaluation_task(db=db, task_id=task_id, task_update=update_data)
        
        # 启动后台评测任务
        background_tasks.add_task(task_processor.process_answer_evaluation, task_id)
        
        return {
            "message": "Evaluation started successfully",
            "task_id": task_id,
            "answers_count": len(answers),
            "status": "evaluating_answers"
        }
        
    except Exception as e:
        logger.error(f"Failed to start evaluation for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start evaluation"
        )


@router.get("/tasks/{task_id}/detailed-results")
def get_task_detailed_results(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务的详细结果，包括配置信息和每道题的得分"""
    task = get_llm_evaluation_task(db=db, task_id=task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # 获取所有LLM答案及其评测结果
    llm_answers = db.query(LLMAnswer).filter(
        LLMAnswer.task_id == task_id
    ).all()
    
    # 构建详细结果
    detailed_answers = []
    total_score = 0
    valid_scores = 0
    
    for answer in llm_answers:
        # 获取标准问题
        std_question = db.query(StdQuestion).filter(
            StdQuestion.id == answer.std_question_id
        ).first()
        
        # 获取评测结果
        evaluations = db.query(Evaluation).filter(
            Evaluation.llm_answer_id == answer.id
        ).all()
        
        # 获取标准答案
        std_answers = []
        if std_question:
            std_answers_data = db.query(StdAnswer).filter(
                StdAnswer.std_question_id == std_question.id
            ).all()
            
            for sa in std_answers_data:
                std_answers.append({
                    "id": sa.id,
                    "answer": sa.answer
                })
        
        # 计算平均分
        answer_scores = [e.score for e in evaluations if e.score is not None]
        avg_score = sum(answer_scores) / len(answer_scores) if answer_scores else None
        
        if avg_score is not None:
            total_score += avg_score
            valid_scores += 1
        
        detailed_answers.append({
            "question_id": answer.std_question_id,
            "question_text": std_question.body if std_question else "未知问题",
            "question_type": getattr(std_question, 'type', 'text') if std_question else 'text',
            "standard_answers": std_answers,
            "llm_answer": {
                "id": answer.id,
                "answer": answer.answer,
                "prompt_used": answer.prompt_used,
                "is_valid": answer.is_valid
            },
            "evaluations": [
                {
                    "id": e.id,
                    "score": float(e.score) if e.score else None,
                    "reasoning": e.reasoning,
                    "evaluator_type": e.evaluator_type.value if e.evaluator_type else None,
                } for e in evaluations
            ],
            "average_score": avg_score
        })      # 计算总体统计并更新任务得分
    overall_average = total_score / valid_scores if valid_scores > 0 else 0
    overall_success_rate = sum(1 for answer in llm_answers if answer.is_valid) / len(llm_answers) if llm_answers else 0
    
    # 更新任务得分到数据库
    if valid_scores > 0:
        task.score = Decimal(str(round(overall_average, 2)))
        db.commit()
        db.refresh(task)
      # 按照前端期望的格式返回数据
    return {
        "task_info": {
            "id": task.id,
            "name": task.name,
            "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
            "progress": task.progress,
            "score": float(task.score) if task.score else None,
            "total_questions": task.total_questions,
            "completed_questions": task.completed_questions,
            "failed_questions": task.failed_questions,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message,
            "dataset_name": task.dataset.name if task.dataset else "Unknown",
            "model_name": task.model.display_name if task.model else "Unknown",
            "model_version": task.model.version if task.model else None
        },
        "configuration": {
            "dataset_name": task.dataset.name if task.dataset else "Unknown",
            "model_name": task.model.display_name if task.model else "Unknown",
            "temperature": float(task.temperature) if task.temperature else 0.7,
            "max_tokens": task.max_tokens or 2000,
            "top_k": task.top_k or 50,
            "enable_reasoning": task.enable_reasoning or False,
            # 兼容前端期望的系统提示词和评估提示词字段
            "system_prompt": task.choice_system_prompt or task.text_system_prompt or task.system_prompt,
            "evaluation_prompt": task.choice_evaluation_prompt or task.text_evaluation_prompt or task.evaluation_prompt
        },
        "prompts": {
            "choice_system_prompt": task.choice_system_prompt,
            "text_system_prompt": task.text_system_prompt,
            "choice_evaluation_prompt": task.choice_evaluation_prompt,
            "text_evaluation_prompt": task.text_evaluation_prompt,
            "system_prompt": task.system_prompt,  # 兼容性保留
            "evaluation_prompt": task.evaluation_prompt  # 兼容性保留
        },
        "statistics": {
            "total_score": float(total_score),
            "average_score": float(overall_average),
            "overall_average_score": float(overall_average),  # 前端期望的字段名
            "success_rate": float(overall_success_rate),
            "completion_rate": float(overall_success_rate),  # 前端期望的字段名
            "valid_scores_count": valid_scores,
            "total_answers": len(llm_answers),
            "valid_answers": sum(1 for answer in llm_answers if answer.is_valid),
            "evaluated_answers": valid_scores
        },
        "detailed_answers": detailed_answers
    }


@router.get("/datasets/{dataset_id}/questions")
def get_dataset_questions(
    dataset_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据集中的问题列表（用于手动录入）"""
    try:
        # 验证数据集是否存在且用户有权限访问
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # 验证数据集是否公开或用户有权限
        if not dataset.is_public and dataset.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to access this dataset"
            )
        
        # 获取问题列表
        questions = db.query(StdQuestion).filter(
            StdQuestion.dataset_id == dataset_id,
            StdQuestion.is_valid == True
        ).offset(skip).limit(limit).all()
        
        # 转换为前端需要的格式
        question_list = []
        for question in questions:
            # 获取标准答案
            std_answer = db.query(StdAnswer).filter(
                StdAnswer.std_question_id == question.id
            ).first()
            
            question_data = {
                "id": question.id,
                "body": question.body,
                "question_type": question.question_type,
                # "choices": question.choices,
                "standard_answer": std_answer.answer if std_answer else None,
            }
            question_list.append(question_data)
        
        return {
            "questions": question_list,
            "total_count": db.query(StdQuestion).filter(
                StdQuestion.dataset_id == dataset_id,
                StdQuestion.is_valid == True
            ).count()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dataset questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dataset questions: {str(e)}"
        )


@router.get("/tasks/{task_id}/manual-evaluation-answers")
def get_task_answers_for_manual_evaluation(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务的答案列表，用于手动评测，包含得分点信息"""
    task = get_llm_evaluation_task(db=db, task_id=task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # 获取所有LLM答案
    llm_answers = db.query(LLMAnswer).filter(
        LLMAnswer.task_id == task_id
    ).all()
    
    # 构建答案列表，包含得分点信息
    answers_data = []
    
    for answer in llm_answers:
        # 获取标准问题
        std_question = db.query(StdQuestion).filter(
            StdQuestion.id == answer.std_question_id
        ).first()
        
        # 获取标准答案及其得分点
        std_answers = []
        if std_question:
            std_answers_data = db.query(StdAnswer).filter(
                StdAnswer.std_question_id == std_question.id
            ).all()
            
            for sa in std_answers_data:
                std_answers.append({
                    "id": sa.id,
                    "answer": sa.answer
                })
        
        # 获取已有的评测结果（如果有的话）
        existing_evaluations = db.query(Evaluation).filter(
            Evaluation.llm_answer_id == answer.id,
            Evaluation.evaluator_type == 'manual'
        ).all()
        
        answers_data.append({
            "llm_answer_id": answer.id,
            "question_id": answer.std_question_id,
            "question_text": std_question.body if std_question else "未知问题",
            "question_type": getattr(std_question, 'type', 'text') if std_question else 'text',
            "standard_answers": std_answers,
            "llm_answer": answer.answer,
            "prompt_used": answer.prompt_used,
            "existing_evaluations": [
                {
                    "id": e.id,
                    "score": float(e.score) if e.score else None,
                    "reasoning": e.reasoning,
                } for e in existing_evaluations
            ]
        })
    
    return {
        "task_id": task_id,
        "task_name": task.name,
        "answers": answers_data,
        "total_count": len(answers_data)
    }
