from sqlalchemy.orm import Session
from .. import models, schemas
from typing import List, Optional

def get_crowdsourced_answer(db: Session, answer_id: int, include_deleted: bool = False) -> Optional[models.CrowdsourcedAnswer]:
    query = db.query(models.ExpertAnswer).filter(models.ExpertAnswer.id == answer_id)
    if not include_deleted:
        query = query.filter(models.ExpertAnswer.is_deleted == False)
    return query.first()

# create_crowdsourced_answer (deferred)

def set_crowdsourced_answer_deleted_status(db: Session, answer_id: int, deleted_status: bool) -> Optional[models.ExpertAnswer]:
    db_answer = db.query(models.ExpertAnswer).filter(models.ExpertAnswer.id == answer_id).first()
    if db_answer:
        db_answer.is_deleted = deleted_status
        db.commit()
        db.refresh(db_answer)
    return db_answer

def set_multiple_crowdsourced_answers_deleted_status(db: Session, answer_ids: List[int], deleted_status: bool) -> int:
    if not answer_ids: 
        return 0
    num_updated = db.query(models.ExpertAnswer).filter(models.ExpertAnswer.id.in_(answer_ids)).update({"is_deleted": deleted_status}, synchronize_session=False)
    db.commit()
    return num_updated