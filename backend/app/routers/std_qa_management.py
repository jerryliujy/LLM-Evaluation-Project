from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..db.database import get_db
from ..crud import crud_std_question, crud_std_answer, crud_relationship_records
from ..models.dataset import Dataset
from ..models.raw_question import RawQuestion
from ..models.raw_answer import RawAnswer
from ..models.expert_answer import ExpertAnswer
from ..schemas.relationship_records import (
    CreateStandardQAWithReferencesRequest, 
    StdQAWithRelationsResponse,
    StdQuestionRawQuestionRecordCreate,
    StdAnswerRawAnswerRecordCreate,
    StdAnswerExpertAnswerRecordCreate
)
from ..schemas.std_question import StdQuestionCreate
from ..schemas.std_answer import StdAnswerCreate
from ..schemas import Msg

router = APIRouter(prefix="/api/std-qa-management", tags=["Standard Q&A Management"])

@router.post("/create-with-relations", response_model=StdQAWithRelationsResponse)
def create_std_qa_with_relations(
    request: CreateStandardQAWithReferencesRequest,
    db: Session = Depends(get_db)
):
    """
    创建标准问答并建立关系记录
    这个API同时创建标准问题、标准答案，并建立与原始数据的关系记录
    """
    try:
        # 验证必要的关联实体是否存在
        if not db.query(Dataset).filter(Dataset.id == request.dataset_id).first():
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # 验证关联的原始问题是否存在
        raw_question_ids = [rel.raw_question_id for rel in request.raw_question_relations]
        if raw_question_ids:
            existing_raw_questions = db.query(RawQuestion.id).filter(
                RawQuestion.id.in_(raw_question_ids)
            ).all()
            existing_ids = [q.id for q in existing_raw_questions]
            missing_ids = set(raw_question_ids) - set(existing_ids)
            if missing_ids:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Raw questions not found: {list(missing_ids)}"
                )
        
        # 验证关联的原始答案是否存在
        raw_answer_ids = [rel.raw_answer_id for rel in request.raw_answer_relations]
        if raw_answer_ids:
            existing_raw_answers = db.query(RawAnswer.id).filter(
                RawAnswer.id.in_(raw_answer_ids)
            ).all()
            existing_ids = [a.id for a in existing_raw_answers]
            missing_ids = set(raw_answer_ids) - set(existing_ids)
            if missing_ids:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Raw answers not found: {list(missing_ids)}"
                )
        
        # 验证关联的专家答案是否存在
        expert_answer_ids = [rel.expert_answer_id for rel in request.expert_answer_relations]
        if expert_answer_ids:
            existing_expert_answers = db.query(ExpertAnswer.id).filter(
                ExpertAnswer.id.in_(expert_answer_ids)
            ).all()
            existing_ids = [a.id for a in existing_expert_answers]
            missing_ids = set(expert_answer_ids) - set(existing_ids)
            if missing_ids:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Expert answers not found: {list(missing_ids)}"
                )
        
        # 1. 创建标准问题
        std_question_data = StdQuestionCreate(
            dataset_id=request.dataset_id,
            question_text=request.question_text,
            difficulty_level=request.difficulty_level,
            knowledge_points=request.knowledge_points,
            tags=request.tags,
            notes=request.notes,
            created_by=request.created_by
        )
        std_question = crud_std_question.create_std_question(db, std_question_data)
        
        # 2. 创建标准答案
        std_answer_data = StdAnswerCreate(
            std_question_id=std_question.id,
            answer_text=request.answer_text,
            answer_type=request.answer_type,
            scoring_points=request.scoring_points,
            total_score=request.total_score,
            explanation=request.explanation,
            created_by=request.created_by
        )
        std_answer = crud_std_answer.create_std_answer(db, std_answer_data)
        
        # 获取数据集当前版本用于答案版本管理
        dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
        if dataset:
            # 更新答案的版本区间字段
            std_answer.original_version_id = dataset.version
            std_answer.current_version_id = dataset.version
            db.commit()
            db.refresh(std_answer)
        
        # 3. 创建关系记录
        created_relations = {
            'raw_question_relations': [],
            'raw_answer_relations': [],
            'expert_answer_relations': []
        }
          # 创建标准问题-原始问题关系记录
        for rel in request.raw_question_relations:
            record_create = StdQuestionRawQuestionRecordCreate(
                std_question_id=std_question.id,
                raw_question_id=rel.raw_question_id,
                notes=rel.notes,
                created_by=request.created_by
            )
            relation_record = crud_relationship_records.create_std_question_raw_question_record(
                db=db,
                record=record_create
            )
            created_relations['raw_question_relations'].append(relation_record)
          # 创建标准答案-原始答案关系记录
        for rel in request.raw_answer_relations:
            record_create = StdAnswerRawAnswerRecordCreate(
                std_answer_id=std_answer.id,
                raw_answer_id=rel.raw_answer_id,
                notes=rel.notes,
                created_by=request.created_by
            )
            relation_record = crud_relationship_records.create_std_answer_raw_answer_record(
                db=db,
                record=record_create
            )
            created_relations['raw_answer_relations'].append(relation_record)
          # 创建标准答案-专家答案关系记录
        for rel in request.expert_answer_relations:
            record_create = StdAnswerExpertAnswerRecordCreate(
                std_answer_id=std_answer.id,
                expert_answer_id=rel.expert_answer_id,
                notes=rel.notes,
                created_by=request.created_by
            )
            relation_record = crud_relationship_records.create_std_answer_expert_answer_record(
                db=db,
                record=record_create
            )
            created_relations['expert_answer_relations'].append(relation_record)
        
        # 提交所有更改
        db.commit()
        
        # 刷新对象以获取最新数据
        db.refresh(std_question)
        db.refresh(std_answer)
        
        return StdQAWithRelationsResponse(
            std_question=std_question,
            std_answer=std_answer,
            raw_question_relations=created_relations['raw_question_relations'],
            raw_answer_relations=created_relations['raw_answer_relations'],
            expert_answer_relations=created_relations['expert_answer_relations']
        )
        
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"Database integrity error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{std_question_id}/with-relations", response_model=StdQAWithRelationsResponse)
def get_std_qa_with_relations(
    std_question_id: int,
    db: Session = Depends(get_db)
):
    """
    获取标准问答及其所有关系记录
    """
    # 获取标准问题
    std_question = crud_std_question.get_std_question(db, std_question_id)
    if not std_question:
        raise HTTPException(status_code=404, detail="Standard question not found")
    
    # 获取标准答案（假设一个问题只有一个答案，如果有多个需要调整）
    std_answer = crud_std_answer.get_std_answers_by_question_id(db, std_question_id)
    if not std_answer:
        raise HTTPException(status_code=404, detail="Standard answer not found")
    
    # 如果返回的是列表，取第一个
    if isinstance(std_answer, list):
        std_answer = std_answer[0] if std_answer else None
    
    if not std_answer:
        raise HTTPException(status_code=404, detail="Standard answer not found")
    
    # 获取关系记录
    raw_question_relations = crud_relationship_records.get_std_question_raw_question_records(
        db, std_question_id=std_question_id
    )
    
    raw_answer_relations = crud_relationship_records.get_std_answer_raw_answer_records(
        db, std_answer_id=std_answer.id
    )
    
    expert_answer_relations = crud_relationship_records.get_std_answer_expert_answer_records(
        db, std_answer_id=std_answer.id
    )
    
    return StdQAWithRelationsResponse(
        std_question=std_question,
        std_answer=std_answer,
        raw_question_relations=raw_question_relations,
        raw_answer_relations=raw_answer_relations,
        expert_answer_relations=expert_answer_relations
    )

@router.delete("/{std_question_id}/with-relations", response_model=Msg)
def delete_std_qa_with_relations(
    std_question_id: int,
    db: Session = Depends(get_db)
):
    """
    删除标准问答及其所有关系记录
    这会软删除标准问题和答案，并删除所有相关的关系记录
    """
    try:
        # 获取标准问题
        std_question = crud_std_question.get_std_question(db, std_question_id)
        if not std_question:
            raise HTTPException(status_code=404, detail="Standard question not found")
        
        # 获取标准答案
        std_answers = crud_std_answer.get_std_answers_by_question_id(db, std_question_id)
        
        # 删除所有关系记录
        for std_answer in std_answers:
            # 删除标准答案-原始答案关系记录
            crud_relationship_records.delete_std_answer_raw_answer_records_by_std_answer(
                db, std_answer.id
            )
            
            # 删除标准答案-专家答案关系记录
            crud_relationship_records.delete_std_answer_expert_answer_records_by_std_answer(
                db, std_answer.id
            )
        
        # 删除标准问题-原始问题关系记录
        crud_relationship_records.delete_std_question_raw_question_records_by_std_question(
            db, std_question_id
        )
        
        # 软删除标准答案
        for std_answer in std_answers:
            crud_std_answer.set_std_answer_deleted_status(db, std_answer.id, True)
        
        # 软删除标准问题
        crud_std_question.set_std_question_deleted_status(db, std_question_id, True)
        
        db.commit()
        
        return Msg(message=f"Standard Q&A {std_question_id} and all relations deleted successfully")
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error deleting standard Q&A with relations: {str(e)}"
        )
