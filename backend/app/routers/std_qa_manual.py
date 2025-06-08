from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.std_question import StdQuestion
from app.models.std_answer import StdAnswer, StdAnswerScoringPoint
from app.models.dataset import Dataset
from app.models.relationship_records import StdAnswerRawAnswerRecord, StdAnswerExpertAnswerRecord
from app.schemas.std_question import StdQuestionCreate
from app.schemas.std_answer import StdAnswerCreate
from app.auth import get_current_active_user
from app.db.database import get_db
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/std-qa", tags=["standard-qa-manual"])

class ManualStdQaCreate(BaseModel):
    dataset_id: int
    question: str
    answer: str
    question_type: str = "text"
    key_points: Optional[List[str]] = None
    raw_question_id: Optional[int] = None
    raw_answer_id: Optional[int] = None
    expert_answer_id: Optional[int] = None

@router.post("/create")
async def create_manual_std_qa(
    std_qa_data: ManualStdQaCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """手动创建标准问答对"""
    
    # 验证数据集存在
    dataset = db.query(Dataset).filter(Dataset.id == std_qa_data.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # 验证用户权限（只有管理员可以创建）
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin users can create standard QA pairs")
    
    try:
        # 创建标准问题
        std_question = StdQuestion(
            dataset_id=std_qa_data.dataset_id,
            raw_question_id=std_qa_data.raw_question_id,
            body=std_qa_data.question,
            question_type=std_qa_data.question_type,
            version=1,
            created_by=current_user.id,
            is_valid=True
        )
        db.add(std_question)
        db.flush()  # 获取ID但不提交事务
          # 创建标准答案
        std_answer = StdAnswer(
            std_question_id=std_question.id,
            answer=std_qa_data.answer,
            answered_by=current_user.id,
            is_valid=True
        )
        db.add(std_answer)
        db.flush()  # 获取ID但不提交事务
        
        # 处理关键点（如果有）
        if std_qa_data.key_points:
            for index, point in enumerate(std_qa_data.key_points):
                scoring_point = StdAnswerScoringPoint(
                    std_answer_id=std_answer.id,
                    answer=point,
                    point_order=index + 1,
                    created_by=current_user.id,
                    is_valid=True
                )
                db.add(scoring_point)
        
        # 处理原始答案关联（如果有）
        if std_qa_data.raw_answer_id:
            raw_answer_record = StdAnswerRawAnswerRecord(
                std_answer_id=std_answer.id,
                raw_answer_id=std_qa_data.raw_answer_id,
                created_by=current_user.id
            )
            db.add(raw_answer_record)
        
        # 处理专家答案关联（如果有）
        if std_qa_data.expert_answer_id:
            expert_answer_record = StdAnswerExpertAnswerRecord(
                std_answer_id=std_answer.id,
                expert_answer_id=std_qa_data.expert_answer_id,
                created_by=current_user.id
            )
            db.add(expert_answer_record)
        
        # 提交事务
        db.commit()
        db.refresh(std_question)
        db.refresh(std_answer)
        
        return {
            "message": "Standard QA pair created successfully",
            "std_question_id": std_question.id,
            "std_answer_id": std_answer.id,
            "question": std_question.body,
            "answer": std_answer.answer
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create standard QA pair: {str(e)}")
