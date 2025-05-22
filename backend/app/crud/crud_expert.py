from sqlalchemy.orm import Session
from .. import models
from typing import Optional

def set_expert_deleted_status(db: Session, expert_id: int, deleted_status: bool) -> Optional[models.Expert]:
    db_expert = db.query(models.Expert).filter(models.Expert.id == expert_id).first()
    if db_expert:
        db_expert.is_deleted = deleted_status
        db.commit()
        db.refresh(db_expert)
    return db_expert