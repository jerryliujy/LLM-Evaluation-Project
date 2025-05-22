from sqlalchemy.orm import Session
from .. import models, schemas
from typing import List, Optional

def get_raw_answer(db: Session, answer_id: int, include_deleted: bool = False) -> Optional[models.RawAnswer]:
    query = db.query(models.RawAnswer).filter(models.RawAnswer.id == answer_id)
    if not include_deleted:
        query = query.filter(models.RawAnswer.is_deleted == False)
    return query.first()

# create_raw_answer (deferred)

def set_raw_answer_deleted_status(db: Session, answer_id: int, deleted_status: bool) -> Optional[models.RawAnswer]:
    db_answer = db.query(models.RawAnswer).filter(models.RawAnswer.id == answer_id).first()
    if db_answer:
        db_answer.is_deleted = deleted_status
        db.commit()
        db.refresh(db_answer)
    return db_answer
    
def set_multiple_raw_answers_deleted_status(db: Session, answer_ids: List[int], deleted_status: bool) -> int:
    if not answer_ids: 
        return 0
    num_updated = db.query(models.RawAnswer).filter(models.RawAnswer.id.in_(answer_ids)).update({"is_deleted": deleted_status}, synchronize_session=False)
    db.commit()
    return num_updated