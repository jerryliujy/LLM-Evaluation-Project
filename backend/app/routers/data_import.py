from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import io
from datetime import datetime

from ..db.database import get_db
from ..models.dataset import Dataset
from ..models.raw_question import RawQuestion
from ..models.raw_answer import RawAnswer
from ..models.expert import Expert
from ..models.expert_answer import ExpertAnswer
from ..models.tag import Tag

router = APIRouter(prefix="/api/data-import", tags=["data-import"])

@router.post("/dataset")
async def create_dataset(
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    """创建新的数据集"""
    
    dataset = Dataset(
        description=description,
        create_time=datetime.now()
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    return {"dataset_id": dataset.id, "description": dataset.description}

@router.post("/upload-questions")
async def upload_questions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传原始问题和回答数据（不关联到任何dataset）"""
    
    # 读取文件内容
    try:
        content = await file.read()
        if file.filename.endswith('.json'):
            data = json.loads(content.decode('utf-8'))
        else:
            raise HTTPException(status_code=400, detail="Only JSON files are supported")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # 处理数据
    imported_questions = 0
    imported_answers = 0
    
    try:
        for item in data:
            # 解析日期
            issued_at = None
            if item.get('issued_at'):
                try:
                    issued_at = datetime.strptime(item['issued_at'], '%Y-%m-%d %H:%M')
                except ValueError:
                    try:
                        issued_at = datetime.strptime(item['issued_at'], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass
              # 创建原始问题
            raw_question = RawQuestion(
                title=item['title'],
                url=item.get('url'),
                body=item.get('body'),
                votes=str(item.get('votes', '0')),  # 确保为str类型
                views=item.get('views'),
                author=item.get('author'),
                tags_json=item.get('tags'),  # 使用tags_json字段
                issued_at=issued_at,
                is_deleted=False
            )
            
            db.add(raw_question)
            db.flush()  # 获取生成的ID
            
            # 处理tags - 创建Tag对象并建立关联
            if item.get('tags') and isinstance(item['tags'], list):
                for tag_label in item['tags']:
                    # 查找或创建标签
                    tag = db.query(Tag).filter(Tag.label == tag_label).first()
                    if not tag:
                        tag = Tag(label=tag_label)
                        db.add(tag)
                        db.flush()
                    
                    # 建立关联
                    if tag not in raw_question.tags:
                        raw_question.tags.append(tag)
            
            imported_questions += 1
            
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
                        upvotes=str(answer_data.get('upvotes', '0')),  # 确保为str类型
                        answered_by=answer_data.get('answered_by'),
                        answered_at=answered_at,
                        is_deleted=False
                    )
                    
                    db.add(raw_answer)
                    imported_answers += 1
        
        db.commit()
        
        return {
            "message": "Raw data imported successfully",
            "imported_questions": imported_questions,
            "imported_answers": imported_answers
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing data: {str(e)}")

@router.get("/datasets")
async def list_datasets(db: Session = Depends(get_db)):
    """获取所有数据集列表"""
    
    datasets = db.query(Dataset).all()
    return [
        {
            "id": dataset.id,
            "description": dataset.description,
            "create_time": dataset.create_time
        }
        for dataset in datasets
    ]

@router.get("/raw-questions")
async def list_raw_questions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取原始问题列表"""
    
    questions = db.query(RawQuestion).filter(
        RawQuestion.is_deleted == False
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
