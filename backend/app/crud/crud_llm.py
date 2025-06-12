"""
CRUD operations for LLM models
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.llm import LLM
from app.schemas.llm import LLMCreate, LLMUpdate


def get_llm(db: Session, llm_id: int) -> Optional[LLM]:
    """获取单个LLM模型"""
    return db.query(LLM).filter(LLM.id == llm_id).first()


def get_llm_by_name(db: Session, name: str) -> Optional[LLM]:
    """根据名称获取LLM模型"""
    return db.query(LLM).filter(LLM.name == name).first()


def get_llms(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[LLM]:
    """获取LLM模型列表"""
    query = db.query(LLM)
    if active_only:
        query = query.filter(LLM.is_active == True)
    return query.offset(skip).limit(limit).all()


def get_active_llms(db: Session) -> List[LLM]:
    """获取所有活跃的LLM模型"""
    return db.query(LLM).filter(LLM.is_active == True).all()


def get_llms_by_provider(db: Session, provider: str) -> List[LLM]:
    """根据提供商获取LLM模型"""
    return db.query(LLM).filter(LLM.provider == provider, LLM.is_active == True).all()


def create_llm(db: Session, llm: LLMCreate) -> LLM:
    """创建新的LLM模型"""
    db_llm = LLM(**llm.dict())
    db.add(db_llm)
    db.commit()
    db.refresh(db_llm)
    return db_llm


def update_llm_status(db: Session, llm_id: int, is_active: bool) -> Optional[LLM]:
    """更新LLM模型状态"""
    db_llm = db.query(LLM).filter(LLM.id == llm_id).first()
    if db_llm:
        db_llm.is_active = is_active
        db.commit()
        db.refresh(db_llm)
    return db_llm


def delete_llm(db: Session, llm_id: int) -> bool:
    """删除LLM模型（软删除，设置为不活跃）"""
    db_llm = db.query(LLM).filter(LLM.id == llm_id).first()
    if db_llm:
        db_llm.is_active = False
        db.commit()
        return True
    return False
