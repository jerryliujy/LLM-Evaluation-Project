from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.std_question import StdQuestion
from app.models.std_answer import StdAnswer, StdAnswerScoringPoint
from app.models.dataset import Dataset
from app.models.tag import Tag
from app.models.relationship_records import StdAnswerRawAnswerRecord, StdAnswerExpertAnswerRecord, StdQuestionRawQuestionRecord
from app.schemas.std_question import StdQuestionCreate
from app.schemas.std_answer import StdAnswerCreate
from app.auth import get_current_active_user
from app.db.database import get_db
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/std-qa", tags=["standard-qa-manual"])

class KeyPointData(BaseModel):
    content: str

class ManualStdQaCreate(BaseModel):
    dataset_id: int
    question: str
    answer: str
    question_type: str = "text"
    key_points: Optional[List[KeyPointData]] = None
    raw_question_ids: Optional[List[int]] = None  # 改为支持多个原始问题
    raw_answer_ids: Optional[List[int]] = None  # 改为支持多个原始回答
    expert_answer_ids: Optional[List[int]] = None  # 改为支持多个专家回答
    tags: Optional[List[str]] = None  # 用户指定的额外标签

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
        # 验证原始问题是否存在
        if std_qa_data.raw_question_ids:
            from app.models.raw_question import RawQuestion
            existing_questions = db.query(RawQuestion.id).filter(
                RawQuestion.id.in_(std_qa_data.raw_question_ids),
                RawQuestion.is_deleted == False
            ).all()
            existing_ids = [q.id for q in existing_questions]
            missing_ids = set(std_qa_data.raw_question_ids) - set(existing_ids)
            if missing_ids:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Raw questions not found: {list(missing_ids)}"
                )

        # 创建标准问题（不直接关联单个原始问题，而是通过关系表）
        std_question = StdQuestion(
            dataset_id=std_qa_data.dataset_id,
            body=std_qa_data.question,
            question_type=std_qa_data.question_type,
            created_by=current_user.id,
            is_valid=True
        )
        db.add(std_question)
        db.flush()  # 获取ID但不提交事务        # 创建标准问题与原始问题的关系记录
        if std_qa_data.raw_question_ids:
            for raw_question_id in std_qa_data.raw_question_ids:                
                question_relation = StdQuestionRawQuestionRecord(
                    std_question_id=std_question.id,
                    raw_question_id=raw_question_id,
                    created_by=current_user.id
                )
                db.add(question_relation)

        # 处理标签：包含原始问题的标签和用户指定的标签
        all_tags = set()
        
        # 1. 从关联的原始问题获取标签
        if std_qa_data.raw_question_ids:
            from app.models.raw_question import RawQuestion
            for raw_question_id in std_qa_data.raw_question_ids:
                raw_question = db.query(RawQuestion).filter(RawQuestion.id == raw_question_id).first()
                if raw_question and raw_question.tags:
                    for tag in raw_question.tags:
                        all_tags.add(tag.label)
        
        # 2. 添加用户指定的标签
        if std_qa_data.tags:
            for tag_label in std_qa_data.tags:
                all_tags.add(tag_label)
        
        # 3. 创建或获取所有标签并关联到标准问题
        for tag_label in all_tags:
            tag = db.query(Tag).filter(Tag.label == tag_label).first()
            if not tag:
                tag = Tag(label=tag_label)
                db.add(tag)
                db.flush()
            
            if tag not in std_question.tags:
                std_question.tags.append(tag)

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
                    answer=point.content,  
                    point_order=index + 1,
                    is_valid=True
                )
                db.add(scoring_point)

        # 处理原始答案关联（如果有）
        if std_qa_data.raw_answer_ids:
            for raw_answer_id in std_qa_data.raw_answer_ids:
                raw_answer_record = StdAnswerRawAnswerRecord(
                    std_answer_id=std_answer.id,
                    raw_answer_id=raw_answer_id,
                    created_by=current_user.id
                )
                db.add(raw_answer_record)
        
        # 处理专家答案关联（如果有）
        if std_qa_data.expert_answer_ids:
            for expert_answer_id in std_qa_data.expert_answer_ids:
                expert_answer_record = StdAnswerExpertAnswerRecord(
                    std_answer_id=std_answer.id,
                    expert_answer_id=expert_answer_id,
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
