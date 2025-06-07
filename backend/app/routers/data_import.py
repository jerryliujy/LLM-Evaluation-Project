from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import json
import io
from datetime import datetime
from pydantic import BaseModel

from ..db.database import get_db
from ..models.dataset import Dataset
from ..models.raw_question import RawQuestion
from ..models.raw_answer import RawAnswer
from ..models.expert_answer import ExpertAnswer
from ..models.tag import Tag
from ..models.user import User
from ..auth import get_current_active_user

router = APIRouter(prefix="/api/data-import", tags=["data-import"])

class JsonDataImport(BaseModel):
    data: List[dict]

@router.post("/dataset")
async def create_dataset(
    name: str = Form(...),
    description: str = Form(...),
    is_public: bool = Form(True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新的数据集"""
    
    dataset = Dataset(
        name=name,
        description=description,
        created_by=current_user.id,
        is_public=is_public
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    return {"dataset_id": dataset.id, "name": dataset.name, "description": dataset.description}

@router.get("/datasets")
async def list_datasets(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户可访问的数据集列表"""
    
    # 管理员可以看到所有数据集，普通用户只能看到自己的和公开的
    if current_user.role == "admin":
        datasets = db.query(Dataset).all()
    else:
        datasets = db.query(Dataset).filter(
            (Dataset.created_by == current_user.id) | (Dataset.is_public == True)
        ).all()
    
    return [
        {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "is_public": dataset.is_public,
            "create_time": dataset.create_time
        }
        for dataset in datasets
    ]

@router.get("/raw-questions")
async def list_raw_questions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的原始问题列表"""
    
    questions = db.query(RawQuestion).filter(
        RawQuestion.is_deleted == False,
        RawQuestion.created_by == current_user.id
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": question.id,
            "title": question.title,
            "url": question.url,
            "votes": question.votes,
            "views": question.views,
            "author": question.author,
            "tags": question.tags,
            "issued_at": question.issued_at,
            "created_at": question.created_at
        }
        for question in questions
    ]

@router.post("/raw-qa")
async def upload_raw_qa_data(
    json_data: JsonDataImport,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """上传原始Q&A数据到当前用户的原始问题池"""
    
    try:
        data = json_data.data
        imported_questions = 0
        imported_answers = 0
        
        for item in data:
            # 处理发布时间
            issued_at = None
            if item.get('issued_at'):
                try:
                    issued_at = datetime.strptime(item['issued_at'], '%Y-%m-%d %H:%M')
                except ValueError:
                    try:
                        issued_at = datetime.strptime(item['issued_at'], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass
            
            # 创建原始问题，关联到当前用户
            raw_question = RawQuestion(
                title=item.get('title', ''),
                body=item.get('body', ''),
                url=item.get('url', ''),
                votes=str(item.get('votes', '0')),
                views=str(item.get('views', '0')),
                author=item.get('author'),
                tags_json=item.get('tags'),
                issued_at=issued_at,
                created_by=current_user.id,  # 关联到当前用户
                is_deleted=False
            )
            
            db.add(raw_question)
            db.flush()
            imported_questions += 1
            
            # 处理标签
            if item.get('tags') and isinstance(item['tags'], list):
                for tag_label in item['tags']:
                    tag = db.query(Tag).filter(Tag.label == tag_label).first()
                    if not tag:
                        tag = Tag(label=tag_label)
                        db.add(tag)
                        db.flush()
                    
                    if tag not in raw_question.tags:
                        raw_question.tags.append(tag)
            
            # 创建原始回答
            if 'answers' in item and isinstance(item['answers'], list):
                for answer_data in item['answers']:
                    answered_at = None
                    if answer_data.get('answered_at'):
                        try:
                            answered_at = datetime.strptime(answer_data['answered_at'], '%Y-%m-%d %H:%M')
                        except ValueError:
                            try:
                                answered_at = datetime.strptime(answer_data['answered_at'], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                pass
                    
                    raw_answer = RawAnswer(
                        question_id=raw_question.id,
                        answer=answer_data.get('answer', ''),
                        upvotes=str(answer_data.get('upvotes', '0')),
                        answered_by=answer_data.get('answered_by'),
                        answered_at=answered_at,
                        is_deleted=False
                    )
                    
                    db.add(raw_answer)
                    imported_answers += 1
        db.commit()
        return {
            "message": f"Raw Q&A data imported successfully to user {current_user.username}'s question pool",
            "user_id": current_user.id,
            "imported_questions": imported_questions,
            "imported_answers": imported_answers
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing raw Q&A data: {str(e)}")

@router.post("/expert-answers/{dataset_id}")
async def upload_expert_answers_data(
    dataset_id: int,
    json_data: JsonDataImport,
    db: Session = Depends(get_db)
):
    """上传专家回答数据到指定数据集"""
    
    # 验证数据集是否存在
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        data = json_data.data
        imported_expert_answers = 0
        imported_questions = 0
        
        for item in data:
            question_id = None
            
            # 如果有question_id，直接使用
            if item.get('question_id'):
                question_id = item['question_id']
                question = db.query(RawQuestion).filter(RawQuestion.id == question_id).first()
                if not question:
                    raise HTTPException(status_code=400, detail=f"Question with ID {question_id} not found")
            else:
                # 如果没有question_id，尝试通过title查找或创建问题
                title = item.get('title', '')
                if not title:
                    raise HTTPException(status_code=400, detail="Either question_id or title must be provided")
                
                # 查找现有问题
                question = db.query(RawQuestion).filter(RawQuestion.title == title).first()
                
                if not question:
                    # 创建新问题
                    issued_at = None
                    if item.get('issued_at'):
                        try:
                            issued_at = datetime.strptime(item['issued_at'], '%Y-%m-%d %H:%M')
                        except ValueError:
                            try:
                                issued_at = datetime.strptime(item['issued_at'], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                pass
                    
                    question = RawQuestion(
                        title=title,
                        body=item.get('body', ''),
                        url=item.get('url', ''),
                        votes=str(item.get('votes', '0')),
                        views=str(item.get('views', '0')),
                        author=item.get('author'),
                        tags_json=item.get('tags'),
                        issued_at=issued_at,
                        is_deleted=False
                    )
                    
                    db.add(question)
                    db.flush()
                    imported_questions += 1
                
                question_id = question.id
            
            # 创建专家回答
            if 'expert_answers' in item and isinstance(item['expert_answers'], list):
                for expert_answer_data in item['expert_answers']:                   
                    expert_answer = ExpertAnswer(
                        question_id=question_id,
                        answer=expert_answer_data.get('content', ''),
                        answered_by=expert_answer_data.get('expert_id', 'Expert'),
                        answered_at=datetime.now(),
                        is_deleted=False
                    )
                    
                    db.add(expert_answer)
                    imported_expert_answers += 1
        
        db.commit()
        return {
            "message": f"Expert answers imported successfully to dataset {dataset.description}",
            "dataset_id": dataset_id,
            "imported_questions": imported_questions,
            "imported_expert_answers": imported_expert_answers
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing expert answers: {str(e)}")

@router.post("/std-qa/{dataset_id}")
async def upload_std_qa_data(
    dataset_id: int,
    json_data: JsonDataImport,
    db: Session = Depends(get_db)
):
    """上传标准Q&A数据到指定数据集（暂未实现）"""
    
    # 验证数据集是否存在
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # TODO: 实现标准Q&A数据导入逻辑
    raise HTTPException(status_code=501, detail="Standard Q&A import not implemented yet")
