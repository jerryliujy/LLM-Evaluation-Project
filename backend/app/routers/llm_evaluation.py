"""
LLM Evaluation Router for regular users
Provides marketplace access, LLM evaluation, and result management
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import uuid
from datetime import datetime

from app.db.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.models.std_question import StdQuestion
from app.models.llm_answer import LLM, LLMAnswer
from app.models.evaluation import Evaluation
from app.schemas.llm_answer import (
    LLM as LLMSchema, LLMCreate, LLMAnswer as LLMAnswerSchema, 
    LLMAnswerCreate, LLMAnswerWithDetails, LLMEvaluationRequest, 
    LLMEvaluationResponse, MarketplaceDatasetInfo, DatasetDownloadResponse
)
from app.schemas.evaluation import EvaluationCreate, EvaluationResponse, BatchEvaluationRequest
from app.crud.crud_llm_answer import (
    get_or_create_llm, create_llm_answer, get_llm_answers_paginated,
    get_llm_answer, update_llm_answer
)
from app.crud.crud_evaluation_new import (
    create_evaluation, get_evaluations_by_llm_answer, batch_create_evaluations,
    get_evaluation_statistics
)
from app.crud.crud_std_question import get_std_questions_paginated

router = APIRouter()


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
        question_data = {
            "id": question.id,
            "body": question.body,
            "question_type": question.question_type,
            "created_at": question.created_at.isoformat(),
            "answers": []
        }
        
        # 添加标准答案
        for answer in question.std_answers:
            if answer.is_valid:
                answer_data = {
                    "id": answer.id,
                    "answer": answer.answer,
                    "answered_at": answer.answered_at.isoformat(),
                    "scoring_points": [
                        {
                            "answer": sp.answer,
                            "point_order": sp.point_order
                        }
                        for sp in answer.scoring_points if sp.is_valid
                    ]
                }
                question_data["answers"].append(answer_data)
        
        questions_data.append(question_data)
    
    # 统计信息
    question_count = len(questions_data)
    
    dataset_info = MarketplaceDatasetInfo(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        version=dataset.version,
        question_count=question_count,
        is_public=dataset.is_public,
        created_by=dataset.created_by,
        create_time=dataset.create_time
    )
    
    return DatasetDownloadResponse(
        dataset_info=dataset_info,
        questions=questions_data
    )


@router.post("/evaluation/upload", response_model=LLMEvaluationResponse)
async def upload_llm_evaluation(
    llm_name: str = Form(...),
    llm_version: str = Form(...),
    dataset_id: int = Form(...),
    answers_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传LLM回答进行评测"""
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
    
    # 验证文件格式
    if not answers_file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JSON files are supported"
        )
    
    try:
        # 读取上传的文件
        content = await answers_file.read()
        answers_data = json.loads(content.decode('utf-8'))
        
        # 获取或创建LLM
        llm = get_or_create_llm(db, LLMCreate(
            name=llm_name,
            version=llm_version,
            affiliation="User Upload"
        ))
        
        # 生成评估ID
        evaluation_id = str(uuid.uuid4())
        created_answers = []
        
        # 处理每个答案
        for answer_data in answers_data.get('answers', []):
            question_id = answer_data.get('question_id')
            answer_text = answer_data.get('answer', '')
            scoring_points = answer_data.get('scoring_points', [])
            
            # 验证问题存在
            question = db.query(StdQuestion).filter(
                StdQuestion.id == question_id,
                StdQuestion.current_dataset_id == dataset_id,
                StdQuestion.is_valid == True
            ).first()
            
            if not question:
                continue
            
            # 创建LLM回答
            llm_answer_create = LLMAnswerCreate(
                llm_id=llm.id,
                std_question_id=question_id,
                answer=answer_text,
                api_request_id=evaluation_id,
                scoring_points=[
                    {"answer": sp.get('answer', ''), "point_order": sp.get('point_order', 0)}
                    for sp in scoring_points
                ]
            )
            
            llm_answer = create_llm_answer(db, llm_answer_create)
            created_answers.append(LLMAnswerSchema.model_validate(llm_answer))
        
        return LLMEvaluationResponse(
            evaluation_id=evaluation_id,
            status="completed",
            created_answers=created_answers,
            evaluation_results={
                "total_answers": len(created_answers),
                "dataset_id": dataset_id,
                "llm_name": llm_name,
                "llm_version": llm_version
            }
        )
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing upload: {str(e)}"
        )


@router.get("/evaluation/answers", response_model=List[LLMAnswerWithDetails])
def get_llm_answers(
    skip: int = 0,
    limit: int = 20,
    llm_id: Optional[int] = None,
    question_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取LLM回答列表"""
    answers, total = get_llm_answers_paginated(
        db=db,
        skip=skip,
        limit=limit,
        llm_id=llm_id,
        std_question_id=question_id,
        include_invalid=False
    )
    
    return [LLMAnswerWithDetails.model_validate(answer) for answer in answers]


@router.post("/evaluation/manual", response_model=EvaluationResponse)
def create_manual_evaluation(
    evaluation_data: EvaluationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建手动评估"""
    # 验证LLM回答存在
    llm_answer = get_llm_answer(db, evaluation_data.llm_answer_id)
    if not llm_answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM answer not found"
        )
    
    # 设置评估者信息
    evaluation_data.evaluator_id = current_user.id
    evaluation_data.evaluator_type = "user"
    
    evaluation = create_evaluation(db, evaluation_data)
    return EvaluationResponse.model_validate(evaluation)


@router.post("/evaluation/auto/{llm_answer_id}", response_model=EvaluationResponse)
def create_auto_evaluation(
    llm_answer_id: int,
    evaluation_criteria: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建自动评估（选择题自动评分）"""
    # 获取LLM回答和对应的问题
    llm_answer = get_llm_answer(db, llm_answer_id)
    if not llm_answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM answer not found"
        )
    
    question = llm_answer.std_question
    
    # 仅对选择题进行自动评分
    if question.question_type != "choice":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automatic evaluation is only supported for choice questions"
        )
      # 智能自动评分逻辑
    standard_answers = [answer.answer.lower().strip() for answer in question.std_answers if answer.is_valid]
    llm_answer_text = llm_answer.answer.lower().strip()
    
    # 计算匹配度
    score = 0
    feedback_details = []
    
    if question.question_type == "choice":
        # 选择题评分 - 精确匹配或包含匹配
        for std_answer in standard_answers:
            if std_answer == llm_answer_text:
                # 精确匹配
                score = 100
                feedback_details.append(f"精确匹配标准答案: {std_answer}")
                break
            elif std_answer in llm_answer_text:
                # 包含匹配
                score = 90
                feedback_details.append(f"部分匹配标准答案: {std_answer}")
            elif llm_answer_text in std_answer:
                # 反向包含匹配
                score = 80
                feedback_details.append(f"答案包含在标准答案中: {std_answer}")
        
        # 如果没有匹配，检查是否有相似的字符
        if score == 0:
            for std_answer in standard_answers:
                # 简单的相似度检查（字符匹配度）
                common_chars = set(std_answer) & set(llm_answer_text)
                similarity = len(common_chars) / max(len(set(std_answer)), len(set(llm_answer_text)), 1)
                if similarity > 0.5:
                    score = max(score, int(similarity * 60))
                    feedback_details.append(f"与标准答案有一定相似度: {similarity:.2f}")
    
    # 生成反馈信息
    if score >= 90:
        result_text = "正确"
    elif score >= 60:
        result_text = "部分正确"
    else:
        result_text = "错误"
    
    feedback = f"自动评测结果: {result_text} (得分: {score}分)\n详情: " + "; ".join(feedback_details) if feedback_details else f"自动评测结果: {result_text}"
    evaluation_data = EvaluationCreate(
        std_question_id=question.id,
        llm_answer_id=llm_answer_id,
        score=score,
        evaluator_type="llm",
        evaluator_id=None,
        evaluation_criteria=evaluation_criteria or "智能自动评测 - 选择题匹配算法",
        feedback=feedback
    )
    
    evaluation = create_evaluation(db, evaluation_data)
    return EvaluationResponse.model_validate(evaluation)


@router.get("/evaluation/statistics/{llm_answer_id}")
def get_answer_evaluation_statistics(
    llm_answer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取LLM回答的评估统计信息"""
    # 验证LLM回答存在
    llm_answer = get_llm_answer(db, llm_answer_id)
    if not llm_answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM answer not found"
        )
    
    stats = get_evaluation_statistics(db, llm_answer_id)
    evaluations = get_evaluations_by_llm_answer(db, llm_answer_id)
    
    return {
        "llm_answer_id": llm_answer_id,
        "statistics": stats,
        "evaluations": [EvaluationResponse.model_validate(eval) for eval in evaluations]
    }


@router.get("/evaluation/results/{evaluation_id}/download")
def download_evaluation_results(
    evaluation_id: str,
    format: str = "json",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载评估结果"""
    # 查找所有相关的LLM回答（通过api_request_id）
    llm_answers = db.query(LLMAnswer).filter(
        LLMAnswer.api_request_id == evaluation_id,
        LLMAnswer.is_valid == True
    ).all()
    
    if not llm_answers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation results not found"
        )
    
    results = []
    for answer in llm_answers:
        evaluations = get_evaluations_by_llm_answer(db, answer.id)
        stats = get_evaluation_statistics(db, answer.id)
        
        result = {
            "question_id": answer.std_question_id,
            "question_body": answer.std_question.body,
            "question_type": answer.std_question.question_type,
            "llm_answer": answer.answer,
            "llm_answer_id": answer.id,
            "evaluations": [
                {
                    "score": eval.score,
                    "evaluator_type": eval.evaluator_type.value,
                    "feedback": eval.feedback,
                    "created_at": eval.created_at.isoformat()
                }
                for eval in evaluations
            ],
            "statistics": stats
        }
        results.append(result)
    
    return {
        "evaluation_id": evaluation_id,
        "results": results,
        "summary": {
            "total_questions": len(results),
            "average_score": sum(r["statistics"]["average_score"] for r in results) / len(results) if results else 0,
            "evaluated_questions": len([r for r in results if r["evaluations"]])
        }
    }
