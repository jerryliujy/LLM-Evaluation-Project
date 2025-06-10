from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..db.database import get_db
from ..models.dataset import Dataset
from ..models.std_question import StdQuestion
from ..models.std_answer import StdAnswer
from ..schemas.common import Msg
from pydantic import BaseModel

router = APIRouter(prefix="/api/datasets", tags=["Dataset Versions"])

class VersionCreate(BaseModel):
    description: str

class VersionResponse(BaseModel):
    id: int
    description: str
    created_at: str
    dataset_id: int

@router.post("/{dataset_id}/versions", response_model=VersionResponse)
def create_dataset_version(
    dataset_id: int,
    version_data: VersionCreate,
    db: Session = Depends(get_db)
):
    """创建数据集的新版本"""
    # 验证数据集是否存在
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # 这里暂时返回一个模拟的版本响应
    # 在实际实现中，你可能需要创建一个Version模型来管理版本
    from datetime import datetime
    return VersionResponse(
        id=1,  # 模拟版本ID
        description=version_data.description,
        created_at=datetime.now().isoformat(),
        dataset_id=dataset_id
    )

@router.get("/{dataset_id}/std-questions-with-answers")
def get_std_questions_with_answers(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """获取数据集中的所有标准问答对"""
    # 验证数据集是否存在
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # 获取标准问题及其关联的答案
    questions = db.query(StdQuestion).options(
        joinedload(StdQuestion.std_answers).joinedload(StdAnswer.scoring_points),
        joinedload(StdQuestion.tags)
    ).filter(
        StdQuestion.dataset_id == dataset_id,
        StdQuestion.is_valid == True
    ).all()
    
    result = []
    for question in questions:
        question_data = {
            "id": question.id,
            "body": question.body,
            "question_type": question.question_type,
            "dataset_id": question.dataset_id,
            "is_valid": question.is_valid,
            "created_at": question.created_at.isoformat() if question.created_at else None,
            "previous_version_id": question.previous_version_id,
            "tags": [tag.label for tag in question.tags] if question.tags else [],
            "std_answers": []
        }
        
        for answer in question.std_answers:
            if answer.is_valid:  # 只包含有效的答案
                answer_data = {
                    "id": answer.id,
                    "answer": answer.answer,
                    "answered_by": answer.answered_by,
                    "std_question_id": answer.std_question_id,
                    "is_valid": answer.is_valid,
                    "answered_at": answer.answered_at.isoformat() if answer.answered_at else None,
                    "previous_version_id": answer.previous_version_id,
                    "scoring_points": []
                }
                
                for point in answer.scoring_points:
                    if point.is_valid:  # 只包含有效的得分点
                        point_data = {
                            "id": point.id,
                            "answer": point.answer,
                            "point_order": point.point_order,
                            "std_answer_id": point.std_answer_id,
                            "is_valid": point.is_valid,
                            "previous_version_id": point.previous_version_id
                        }
                        answer_data["scoring_points"].append(point_data)
                
                question_data["std_answers"].append(answer_data)
        
        result.append(question_data)
    
    return result

class StdQuestionVersionUpdate(BaseModel):
    body: str
    question_type: str
    tags: List[str] = []
    std_answers: List[dict] = []

@router.put("/versions/{version_id}/std-questions/{question_id}")
def update_std_question_version(
    version_id: int,
    question_id: int,
    update_data: StdQuestionVersionUpdate,
    db: Session = Depends(get_db)
):
    """在版本编辑模式下更新标准问题"""
    # 获取原始问题
    original_question = db.query(StdQuestion).filter(StdQuestion.id == question_id).first()
    if not original_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # 在实际实现中，这里应该创建新版本的记录
    # 现在暂时直接更新原记录作为演示
    original_question.body = update_data.body
    original_question.question_type = update_data.question_type
    
    # 处理标签更新（这里简化处理）
    # 在实际实现中需要更复杂的标签关系管理
    
    # 处理答案更新
    for answer_data in update_data.std_answers:
        if "id" in answer_data and answer_data["id"]:
            # 更新现有答案
            answer = db.query(StdAnswer).filter(StdAnswer.id == answer_data["id"]).first()
            if answer:
                answer.answer = answer_data.get("answer", answer.answer)
                answer.answered_by = answer_data.get("answered_by", answer.answered_by)
        else:
            # 创建新答案
            new_answer = StdAnswer(
                std_question_id=question_id,
                answer=answer_data.get("answer", ""),
                answered_by=answer_data.get("answered_by"),
                is_valid=True
            )
            db.add(new_answer)
    
    db.commit()
    db.refresh(original_question)
    
    return {"message": "Question updated successfully"}

@router.delete("/versions/{version_id}/std-questions/{question_id}")
def delete_std_question_version(
    version_id: int,
    question_id: int,
    db: Session = Depends(get_db)
):
    """在版本编辑模式下删除标准问题"""
    question = db.query(StdQuestion).filter(StdQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # 软删除
    question.is_valid = False
    
    # 同时软删除关联的答案
    for answer in question.std_answers:
        answer.is_valid = False
        for point in answer.scoring_points:
            point.is_valid = False
    
    db.commit()
    return {"message": "Question deleted successfully"}

class StdQACreate(BaseModel):
    question: dict
    answer: dict

@router.post("/versions/{version_id}/std-qa")
def create_std_qa_version(
    version_id: int,
    qa_data: StdQACreate,
    db: Session = Depends(get_db)
):
    """在版本编辑模式下创建新的标准问答对"""
    # 创建问题
    question_data = qa_data.question
    new_question = StdQuestion(
        dataset_id=question_data.get("dataset_id"),  # 需要从版本信息中获取
        body=question_data.get("body"),
        question_type=question_data.get("question_type", "text"),
        is_valid=True
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    
    # 创建答案
    answer_data = qa_data.answer
    new_answer = StdAnswer(
        std_question_id=new_question.id,
        answer=answer_data.get("answer"),
        answered_by=answer_data.get("answered_by"),
        is_valid=True
    )
    db.add(new_answer)
    db.commit()
    db.refresh(new_answer)
    
    return {
        "id": new_question.id,
        "body": new_question.body,
        "question_type": new_question.question_type,
        "std_answers": [{
            "id": new_answer.id,
            "answer": new_answer.answer,
            "answered_by": new_answer.answered_by
        }]
    }

class ImportData(BaseModel):
    data: List[dict]

@router.post("/versions/{version_id}/import")
def import_data_version(
    version_id: int,
    import_data: ImportData,
    db: Session = Depends(get_db)
):
    """在版本编辑模式下导入数据"""
    imported_count = 0
    
    for item in import_data.data:
        try:
            # 创建问题
            new_question = StdQuestion(
                dataset_id=item.get("dataset_id"),  # 需要从版本信息中获取
                body=item.get("body"),
                question_type=item.get("question_type", "text"),
                is_valid=True
            )
            db.add(new_question)
            db.commit()
            db.refresh(new_question)
            
            # 创建答案
            if "answer" in item:
                new_answer = StdAnswer(
                    std_question_id=new_question.id,
                    answer=item.get("answer"),
                    answered_by=item.get("answered_by"),
                    is_valid=True
                )
                db.add(new_answer)
                db.commit()
            
            imported_count += 1
            
        except Exception as e:
            print(f"Error importing item: {e}")
            continue
    
    return {"imported": imported_count}

@router.post("/versions/{version_id}/commit")
def commit_version(
    version_id: int,
    db: Session = Depends(get_db)
):
    """提交版本更改"""
    # 在实际实现中，这里应该完成版本的最终确认
    # 比如更新版本状态、创建版本快照等
    return {"message": "Version committed successfully"}
