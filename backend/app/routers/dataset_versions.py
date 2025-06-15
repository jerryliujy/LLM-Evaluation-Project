# filepath: d:\classes\Database\PJ\backend\app\routers\dataset_versions.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from ..db.database import get_db
from ..auth import get_current_active_user
from ..models.dataset import Dataset
from ..models.version_tables import (
    VersionStdQuestion, 
    VersionStdAnswer, 
    VersionScoringPoint,
    VersionTag
)
from ..models.std_question import StdQuestion
from ..models.std_answer import StdAnswer, StdAnswerScoringPoint
from ..models.tag import Tag
from ..schemas.std_question import StdQuestionResponse
from ..schemas.std_answer import StdAnswerResponse

router = APIRouter(prefix="/api/datasets", tags=["Dataset Versions"])
version_router = APIRouter(prefix="/api/versions", tags=["Versions"])

def get_version_question_data(db: Session, version_question: VersionStdQuestion):
    """获取版本问题的完整数据"""
    # 获取问题数据：如果被修改则使用修改后的数据，否则使用原始数据
    if version_question.is_modified or version_question.is_new:
        question_body = version_question.modified_body
        question_type = version_question.modified_question_type
    else:
        question_body = version_question.original_question.body  # 使用body字段
        question_type = version_question.original_question.question_type
    question_data = {
        "id": version_question.id,
        "body": question_body,
        "question_type": question_type,
        "tags": [version_tag.tag_label for version_tag in version_question.version_tags if not version_tag.is_deleted],
        "std_answers": [],
        "is_modified": version_question.is_modified,
        "is_new": version_question.is_new
    }
    
    # 处理答案
    for version_answer in version_question.version_answers:
        if not version_answer.is_deleted:
            # 获取答案数据
            if version_answer.is_new or version_answer.is_modified:
                answer_text = version_answer.modified_answer
                answered_by = version_answer.modified_answered_by
            else:
                answer_text = version_answer.original_answer.answer
                answered_by = version_answer.original_answer.created_by  # 使用created_by字段
            
            answer_data = {
                "id": version_answer.id,
                "answer": answer_text,
                "answered_by": answered_by,
                "scoring_points": [],
                "is_modified": version_answer.is_modified,
                "is_new": version_answer.is_new
            }
            
            # 处理得分点
            for version_point in version_answer.version_scoring_points:
                if not version_point.is_deleted:
                    if version_point.is_new or version_point.is_modified:
                        point_answer = version_point.modified_answer
                        point_order = version_point.modified_point_order
                    else:
                        point_answer = version_point.original_point.answer  
                        point_order = version_point.original_point.point_order
                    
                    point_data = {
                        "id": version_point.id,
                        "answer": point_answer,
                        "point_order": point_order,
                        "is_modified": version_point.is_modified,
                        "is_new": version_point.is_new
                    }
                    answer_data["scoring_points"].append(point_data)
            
            question_data["std_answers"].append(answer_data)
    
    return question_data

def copy_dataset_to_version_tables(db: Session, dataset_id: int, version_id: int):
    """将数据集内容复制到版本工作表 - 只记录引用，不复制内容"""
    
    # 获取源数据集的所有标准问题
    source_questions = db.query(StdQuestion).options(
        joinedload(StdQuestion.std_answers).joinedload(StdAnswer.scoring_points),
        joinedload(StdQuestion.tags)
    ).filter(
        StdQuestion.dataset_id == dataset_id,
        StdQuestion.is_valid == True
    ).all()
    
    # 为每个问题创建版本记录（初始状态：未修改）
    for source_question in source_questions:
        # 创建版本问题记录 - 只记录引用，不复制内容
        version_question = VersionStdQuestion(
            version_id=version_id,
            original_question_id=source_question.id,
            is_modified=False,
            is_new=False,
            is_deleted=False
        )
        db.add(version_question)
        db.flush()  # 获取版本问题的ID
        
        # 复制标签到版本表
        for tag in source_question.tags:
            version_tag = VersionTag(
                version_id=version_id,
                version_question_id=version_question.id,
                tag_label=tag.label,
                is_deleted=False,
                is_new=False
            )
            db.add(version_tag)
        
        # 为每个答案创建版本记录
        for source_answer in source_question.std_answers:
            if source_answer.is_valid:
                version_answer = VersionStdAnswer(
                    version_id=version_id,
                    version_question_id=version_question.id,
                    original_answer_id=source_answer.id,
                    is_modified=False,
                    is_deleted=False,
                    is_new=False
                )
                db.add(version_answer)
                db.flush()  # 获取版本答案的ID
                
                # 为每个得分点创建版本记录
                for source_point in source_answer.scoring_points:
                    if source_point.is_valid:
                        version_point = VersionScoringPoint(
                            version_id=version_id,
                            version_answer_id=version_answer.id,
                            original_point_id=source_point.id,
                            is_modified=False,
                            is_deleted=False,
                            is_new=False
                        )
                        db.add(version_point)

@router.post("/{dataset_id}/versions", response_model=DatasetVersionResponse)
def create_dataset_version(
    dataset_id: int,
    version_data: DatasetVersionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """创建数据集的新版本（使用版本工作表）"""
    
    # 验证原始数据集是否存在
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # 获取下一个版本号（字符串格式）
    existing_versions = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id
    ).all()
    
    # 生成版本号，格式为 v1, v2, v3...
    version_number = f"v{len(existing_versions) + 1}"
    
    # 创建版本记录
    new_version = DatasetVersion(
        dataset_id=dataset_id,
        name=version_data.name,
        description=version_data.description,
        version_number=version_number,
        created_by=current_user.id,
        is_committed=False,
        is_public=False
    )
    
    db.add(new_version)
    db.flush()  # 获取版本ID
    
    # 复制原数据库的内容到版本工作表
    copy_dataset_to_version_tables(db, dataset_id, new_version.id)
    
    db.commit()
    db.refresh(new_version)
    
    return new_version

@version_router.get("/{version_id}", response_model=DatasetVersionResponse)
def get_version(version_id: int, db: Session = Depends(get_db)):
    """获取版本信息"""
    version = db.query(DatasetVersion).filter(DatasetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version

@version_router.get("/{version_id}/std-qa")
def get_version_std_qa(version_id: int, db: Session = Depends(get_db)):
    """获取版本中的标准问答对 - 合并原始数据和修改数据"""
    version = db.query(DatasetVersion).filter(DatasetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
      # 获取版本工作表中的问答对
    version_questions = db.query(VersionStdQuestion).options(
        joinedload(VersionStdQuestion.version_answers).joinedload(VersionStdAnswer.version_scoring_points),
        joinedload(VersionStdQuestion.version_tags),
        joinedload(VersionStdQuestion.original_question).joinedload(StdQuestion.std_answers).joinedload(StdAnswer.scoring_points),
        joinedload(VersionStdQuestion.original_question).joinedload(StdQuestion.tags)
    ).filter(
        VersionStdQuestion.version_id == version_id,
        VersionStdQuestion.is_deleted == False
    ).all()
    
    result = []
    for version_question in version_questions:
        # 获取问题数据：如果被修改则使用修改后的数据，否则使用原始数据
        if version_question.is_modified:
            question_body = version_question.modified_body
            question_type = version_question.modified_question_type
        else:
            question_body = version_question.original_question.body
            question_type = version_question.original_question.question_type
        question_data = {
            "id": version_question.id,  # 使用版本表的ID
            "body": question_body,
            "question_type": question_type,
            "tags": [version_tag.tag_label for version_tag in version_question.version_tags if not version_tag.is_deleted],
            "std_answers": [],
            "is_modified": version_question.is_modified
        }
        
        # 处理答案
        for version_answer in version_question.version_answers:
            if not version_answer.is_deleted:
                # 获取答案数据：如果是新增或修改则使用修改后的数据，否则使用原始数据
                if version_answer.is_new or version_answer.is_modified:
                    answer_text = version_answer.modified_answer
                    answered_by = version_answer.modified_answered_by
                else:
                    answer_text = version_answer.original_answer.answer
                    answered_by = version_answer.original_answer.answered_by
                
                answer_data = {
                    "id": version_answer.id,  # 使用版本表的ID
                    "answer": answer_text,
                    "answered_by": answered_by,
                    "scoring_points": [],
                    "is_modified": version_answer.is_modified,
                    "is_new": version_answer.is_new
                }
                
                # 处理得分点
                for version_point in version_answer.version_scoring_points:
                    if not version_point.is_deleted:
                        # 获取得分点数据
                        if version_point.is_new or version_point.is_modified:
                            point_answer = version_point.modified_answer
                            point_order = version_point.modified_point_order
                        else:
                            point_answer = version_point.original_point.answer
                            point_order = version_point.original_point.point_order
                        
                        point_data = {
                            "id": version_point.id,  # 使用版本表的ID
                            "answer": point_answer,
                            "point_order": point_order,
                            "is_modified": version_point.is_modified,
                            "is_new": version_point.is_new
                        }
                        answer_data["scoring_points"].append(point_data)
                
                question_data["std_answers"].append(answer_data)
        
        result.append(question_data)
    
    return result

@version_router.put("/{version_id}/std-questions/{question_id}")
def update_version_question(
    version_id: int,
    question_id: int,
    question_data: dict,
    db: Session = Depends(get_db)
):
    """更新版本中的问题 - 标记为已修改并保存修改内容"""
    version = db.query(DatasetVersion).filter(DatasetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # 更新版本工作表中的问题
    version_question = db.query(VersionStdQuestion).filter(
        and_(
            VersionStdQuestion.id == question_id,
            VersionStdQuestion.version_id == version_id,
            VersionStdQuestion.is_deleted == False
        )
    ).first()
    
    if not version_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # 标记为已修改并保存修改内容
    version_question.is_modified = True
    version_question.modified_body = question_data.get("body")
    version_question.modified_question_type = question_data.get("question_type")
      # 更新标签
    if "tags" in question_data:
        # 删除现有标签
        for version_tag in version_question.version_tags:
            version_tag.is_deleted = True
        
        # 添加新标签
        for tag_label in question_data["tags"]:
            # 确保标签存在于Tag表中
            tag = db.query(Tag).filter(Tag.label == tag_label).first()
            if not tag:
                tag = Tag(label=tag_label)
                db.add(tag)
                db.flush()
            
            # 检查是否已存在该标签的版本记录
            existing_version_tag = next(
                (vt for vt in version_question.version_tags if vt.tag_label == tag_label), 
                None
            )
            
            if existing_version_tag:
                # 恢复已删除的标签
                existing_version_tag.is_deleted = False
            else:
                # 创建新的版本标签记录
                new_version_tag = VersionTag(
                    version_id=version_id,
                    version_question_id=version_question.id,
                    tag_label=tag_label,
                    is_deleted=False,
                    is_new=True
                )
                db.add(new_version_tag)
    
    # 更新答案
    if "std_answers" in question_data:
        # 标记所有现有答案为删除
        for answer in version_question.version_answers:
            answer.is_deleted = True
        
        # 添加新答案
        for answer_data in question_data["std_answers"]:
            # 检查是否是现有答案的修改
            existing_answer = None
            if "id" in answer_data and not answer_data.get("is_new", False):
                existing_answer = next((a for a in version_question.version_answers if a.id == answer_data["id"]), None)
            
            if existing_answer:
                # 修改现有答案
                existing_answer.is_deleted = False
                existing_answer.is_modified = True
                existing_answer.modified_answer = answer_data.get("answer", "")
                existing_answer.modified_answered_by = answer_data.get("answered_by")
                
                # 处理得分点
                for point in existing_answer.version_scoring_points:
                    point.is_deleted = True
                for point_data in answer_data.get("scoring_points", []):
                    if "id" in point_data and not point_data.get("is_new", False):
                        # 修改现有得分点
                        existing_point = next((p for p in existing_answer.version_scoring_points if p.id == point_data["id"]), None)
                        if existing_point:
                            existing_point.is_deleted = False
                            existing_point.is_modified = True
                            existing_point.modified_answer = point_data.get("answer", "")
                            existing_point.modified_point_order = point_data.get("point_order", 1)
                    else:
                        # 新增得分点
                        new_point = VersionScoringPoint(
                            version_id=version_id,
                            version_answer_id=existing_answer.id,
                            is_new=True,
                            is_modified=False,
                            is_deleted=False,
                            modified_answer=point_data.get("answer", ""),
                            modified_point_order=point_data.get("point_order", 1)
                        )
                        db.add(new_point)
            else:
                # 新增答案
                new_answer = VersionStdAnswer(
                    version_id=version_id,
                    version_question_id=version_question.id,
                    is_new=True,
                    is_modified=False,
                    is_deleted=False,
                    modified_answer=answer_data.get("answer", ""),
                    modified_answered_by=answer_data.get("answered_by")
                )
                db.add(new_answer)
                db.flush()
                
                # 添加得分点
                for point_data in answer_data.get("scoring_points", []):
                    new_point = VersionScoringPoint(
                        version_id=version_id,
                        version_answer_id=new_answer.id,
                        is_new=True,
                        is_modified=False,
                        is_deleted=False,
                        modified_answer=point_data.get("answer", ""),
                        modified_point_order=point_data.get("point_order", 1)
                    )
                    db.add(new_point)
    
    db.commit()
    
    # 返回更新后的问题数据
    return get_version_question_data(db, version_question)

@version_router.delete("/{version_id}/std-questions/{question_id}")
def delete_version_question(
    version_id: int,
    question_id: int,
    db: Session = Depends(get_db)
):
    """删除版本中的问题（软删除）"""
    version = db.query(DatasetVersion).filter(DatasetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # 在版本工作表中软删除问题
    version_question = db.query(VersionStdQuestion).filter(
        and_(
            VersionStdQuestion.id == question_id,
            VersionStdQuestion.version_id == version_id,
            VersionStdQuestion.is_deleted == False
        )
    ).first()
    
    if not version_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # 软删除问题和相关答案
    version_question.is_deleted = True
    for answer in version_question.version_answers:
        answer.is_deleted = True
        for point in answer.version_scoring_points:
            point.is_deleted = True
    
    db.commit()
    
    return {"message": "Question deleted successfully"}

@version_router.post("/{version_id}/std-qa")
def create_version_qa(
    version_id: int,
    qa_data: dict,
    db: Session = Depends(get_db)
):
    """在版本中创建新的问答对"""
    version = db.query(DatasetVersion).filter(DatasetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
      # 创建新的版本问题（新增的问题直接设置为修改状态）
    new_question = VersionStdQuestion(
        version_id=version_id,
        is_modified=True,  # 新增的问题标记为已修改
        is_deleted=False,
        modified_body=qa_data["question"]["body"],
        modified_question_type=qa_data["question"].get("question_type", "text")
    )
    db.add(new_question)
    db.flush()
    
    # 添加标签
    for tag_label in qa_data["question"].get("tags", []):
        # 确保标签存在于Tag表中
        tag = db.query(Tag).filter(Tag.label == tag_label).first()
        if not tag:
            tag = Tag(label=tag_label)
            db.add(tag)
            db.flush()
        
        # 创建版本标签记录
        version_tag = VersionTag(
            version_id=version_id,
            version_question_id=new_question.id,
            tag_label=tag_label,
            is_deleted=False,
            is_new=True
        )
        db.add(version_tag)
    
    # 创建答案
    answer_data = qa_data["answer"]
    new_answer = VersionStdAnswer(
        version_id=version_id,
        version_question_id=new_question.id,
        is_new=True,  # 新增的答案
        is_modified=False,
        is_deleted=False,
        modified_answer=answer_data["answer"],
        modified_answered_by=answer_data.get("answered_by")
    )
    db.add(new_answer)
    db.flush()
    
    # 添加得分点
    for point_data in answer_data.get("scoring_points", []):
        new_point = VersionScoringPoint(
            version_id=version_id,
            version_answer_id=new_answer.id,
            is_new=True,  # 新增的得分点
            is_modified=False,
            is_deleted=False,
            modified_answer=point_data.get("answer", ""),
            modified_point_order=point_data.get("point_order", 1)
        )
        db.add(new_point)
    
    db.commit()
    
    # 返回创建的问答对
    return get_version_question_data(db, new_question)

@version_router.post("/{version_id}/commit")
def commit_version(
    version_id: int,
    publish_data: DatasetVersionPublish,
    db: Session = Depends(get_db)
):
    """提交版本（智能创建新数据集，未修改数据通过引用节省存储）"""
    version = db.query(DatasetVersion).filter(DatasetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    if version.is_committed:
        raise HTTPException(status_code=400, detail="Version already committed")
    
    try:
        # 1. 获取原始数据集
        original_dataset = db.query(Dataset).filter(Dataset.id == version.dataset_id).first()
        if not original_dataset:
            raise HTTPException(status_code=404, detail="Original dataset not found")
        
        # 2. 创建新的数据集版本
        new_dataset = Dataset(
            name=original_dataset.name,  # 保持数据集名称一致
            description=f"{original_dataset.description} - 版本 {version.version_number}: {version.description}",
            is_public=publish_data.is_public,
            created_by=original_dataset.created_by
        )
        db.add(new_dataset)
        db.flush()
        
        # 3. 更新版本记录，设置前后版本关系
        version.previous_dataset_id = original_dataset.id
        version.new_dataset_id = new_dataset.id
        
        # 4. 处理版本工作表中的数据
        version_questions = db.query(VersionStdQuestion).options(
            joinedload(VersionStdQuestion.version_answers).joinedload(VersionStdAnswer.version_scoring_points),
            joinedload(VersionStdQuestion.version_tags),
            joinedload(VersionStdQuestion.original_question).joinedload(StdQuestion.std_answers).joinedload(StdAnswer.scoring_points),
            joinedload(VersionStdQuestion.original_question).joinedload(StdQuestion.tags)
        ).filter(
            VersionStdQuestion.version_id == version_id,
            VersionStdQuestion.is_deleted == False
        ).all()
        
        from ..models.tag import Tag
        
        for version_question in version_questions:
            if version_question.is_modified or version_question.is_new:
                # 情况1：修改的问题或新增的问题 - 创建新记录
                if version_question.original_question_id and version_question.is_modified:
                    # 修改的问题：设置previous_version_id
                    new_question = StdQuestion(
                        dataset_id=new_dataset.id,  # 当前所在的数据集ID
                        raw_question_id=version_question.original_question.raw_question_id,  # 兼容字段
                        body=version_question.modified_body,  # 使用body字段而不是text
                        question_type=version_question.modified_question_type,
                        is_valid=True,
                        created_by=version_question.original_question.created_by,
                        version=version_question.original_question.version + 1,
                        previous_version_id=version_question.original_question_id,
                        # 版本管理字段
                        original_version_id=version_question.original_question.original_version_id,
                        current_version_id=version_id
                    )
                else:
                    # 新增的问题
                    new_question = StdQuestion(
                        dataset_id=new_dataset.id,  # 当前所在的数据集ID
                        raw_question_id=1,  # 临时值，实际应该从原始问题获取
                        body=version_question.modified_body,  # 使用body字段而不是text
                        question_type=version_question.modified_question_type,
                        is_valid=True,
                        created_by="version_creation",
                        version=1,
                        # 版本管理字段
                        original_version_id=version_id,
                        current_version_id=version_id
                    )
                
                db.add(new_question)
                db.flush()
                
                # 处理标签
                for version_tag in version_question.version_tags:
                    if not version_tag.is_deleted:
                        tag = db.query(Tag).filter(Tag.label == version_tag.tag_label).first()
                        if not tag:
                            tag = Tag(label=version_tag.tag_label)
                            db.add(tag)
                            db.flush()
                        new_question.tags.append(tag)
                
                # 处理答案
                for version_answer in version_question.version_answers:
                    if not version_answer.is_deleted:
                        if version_answer.is_new or version_answer.is_modified:
                            # 新增或修改的答案
                            new_answer = StdAnswer(
                                std_question_id=new_question.id,
                                answer=version_answer.modified_answer,
                                is_valid=True,
                                created_by=str(version_answer.modified_answered_by) if version_answer.modified_answered_by else "version_creation",
                                version=1 if version_answer.is_new else (version_answer.original_answer.version + 1),
                                previous_version_id=version_answer.original_answer_id if version_answer.is_modified else None
                            )
                            db.add(new_answer)
                            db.flush()
                            
                            # 处理得分点
                            for version_point in version_answer.version_scoring_points:
                                if not version_point.is_deleted:
                                    new_point = StdAnswerScoringPoint(
                                        std_answer_id=new_answer.id,
                                        answer=version_point.modified_answer,
                                        point_order=version_point.modified_point_order,
                                        is_valid=True,
                                        answered_by="version_creation",
                                        version=1 if version_point.is_new else (version_point.original_point.version + 1),
                                        previous_version_id=version_point.original_point_id if version_point.is_modified else None
                                    )
                                    db.add(new_point)
            else:
                # 情况2：未修改的问题 - 更新数据集引用，节省存储
                original_question = version_question.original_question
                original_question.dataset_id = new_dataset.id  # 更新当前所在的数据集ID
                original_question.current_version_id = version_id
        
        # 5. 更新版本状态
        version.is_committed = True
        version.committed_at = func.now()
        
        db.commit()
        
        return {
            "message": "Version committed successfully", 
            "is_public": publish_data.is_public,
            "dataset_id": version.dataset_id,
            "new_dataset_id": new_dataset.id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to commit version: {str(e)}")

@version_router.post("/{version_id}/import")
def import_data_to_version(
    version_id: int,
    import_data: dict,
    db: Session = Depends(get_db)
):
    """导入数据到版本工作表"""
    version = db.query(DatasetVersion).filter(DatasetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    try:
        data_list = import_data.get("data", [])
        imported_count = 0
        
        for item in data_list:
            # 创建版本问题（导入的数据标记为修改状态）
            new_question = VersionStdQuestion(
                version_id=version_id,
                is_modified=True,  # 导入的数据标记为已修改
                is_deleted=False,
                modified_body=item.get("body", ""),
                modified_question_type=item.get("question_type", "text")
            )
            db.add(new_question)
            db.flush()
            
            # 添加标签
            for tag_label in item.get("tags", []):
                # 确保标签存在于Tag表中
                tag = db.query(Tag).filter(Tag.label == tag_label).first()
                if not tag:
                    tag = Tag(label=tag_label)
                    db.add(tag)
                    db.flush()
                
                # 创建版本标签记录
                version_tag = VersionTag(
                    version_id=version_id,
                    version_question_id=new_question.id,
                    tag_label=tag_label,
                    is_deleted=False,
                    is_new=True
                )
                db.add(version_tag)
            
            # 创建答案
            if item.get("answer"):
                new_answer = VersionStdAnswer(
                    version_id=version_id,
                    version_question_id=new_question.id,
                    is_new=True,  # 导入的答案标记为新增
                    is_modified=False,
                    is_deleted=False,
                    modified_answer=item.get("answer", ""),
                    modified_answered_by=item.get("answered_by")
                )
                db.add(new_answer)
                db.flush()
                
                # 添加得分点
                for point_data in item.get("scoring_points", []):
                    new_point = VersionScoringPoint(
                        version_id=version_id,
                        version_answer_id=new_answer.id,
                        is_new=True,  # 导入的得分点标记为新增
                        is_modified=False,
                        is_deleted=False,
                        modified_answer=point_data.get("answer", ""),
                        modified_point_order=point_data.get("point_order", 1)
                    )
                    db.add(new_point)
            
            imported_count += 1
        
        db.commit()
        
        return {
            "message": f"Successfully imported {imported_count} items",
            "imported": imported_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
