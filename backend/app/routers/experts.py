from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from ..models.expert import Expert
from ..crud import crud_expert
from ..schemas.expert import Expert as ExpertSchema, ExpertCreate, ExpertLogin, ExpertLoginResponse
from ..schemas.common import Msg
from ..db.database import get_db

router = APIRouter(
    prefix="/api/experts",
    tags=["Experts"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[ExpertSchema])
def get_all_experts(include_deleted: bool = False, db: Session = Depends(get_db)):
    """获取所有专家列表"""
    experts = crud_expert.get_all_experts(db, include_deleted=include_deleted)
    return experts

@router.post("/", response_model=ExpertSchema)
def create_expert(expert: ExpertCreate, db: Session = Depends(get_db)):
    """创建新的专家账号"""
    # 检查邮箱是否已存在
    existing_expert = db.query(Expert).filter(
        Expert.email == expert.email
    ).first()
    if existing_expert:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_expert = crud_expert.create_expert(db=db, expert=expert)
    return db_expert

@router.post("/login", response_model=ExpertLoginResponse)
def login_expert(login_data: ExpertLogin, db: Session = Depends(get_db)):
    """专家登录"""
    expert = crud_expert.verify_expert_login(
        db, email=login_data.email, password=login_data.password
    )
    if not expert:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 简化版登录，生成简单的token
    token = f"expert_token_{expert.id}_{expert.email}"
    return ExpertLoginResponse(
        expert=expert,
        access_token=token,
        token_type="bearer"
    )

@router.get("/{expert_id}", response_model=ExpertSchema)
def get_expert(expert_id: int, db: Session = Depends(get_db)):
    """获取专家信息"""
    db_expert = crud_expert.get_expert(db, expert_id=expert_id)
    if db_expert is None:
        raise HTTPException(status_code=404, detail="Expert not found")
    return db_expert

@router.delete("/{expert_id}/", response_model=Msg)
def delete_expert_api(expert_id: int, db: Session = Depends(get_db)):
    db_expert = crud_expert.set_expert_deleted_status(db, expert_id=expert_id, deleted_status=True)
    if db_expert is None:
        raise HTTPException(status_code=404, detail="Expert not found")
    return Msg(message=f"Expert {expert_id} marked as deleted")

@router.post("/{expert_id}/restore", response_model=ExpertSchema)
def restore_expert_api(expert_id: int, db: Session = Depends(get_db)):
    """恢复专家账号"""
    # 检查专家是否存在
    db_expert = db.query(Expert).filter(Expert.id == expert_id).first()
    if not db_expert:
        raise HTTPException(status_code=404, detail="Expert not found")
    
    if not db_expert.is_deleted:
        raise HTTPException(status_code=400, detail="Expert is not deleted")
    
    restored_expert = crud_expert.set_expert_deleted_status(
        db, expert_id=expert_id, deleted_status=False
    )
    if restored_expert is None:
        raise HTTPException(status_code=404, detail="Error restoring expert")
    
    return restored_expert
