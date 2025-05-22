from sqlalchemy.orm import Session, selectinload
from .. import models, schemas
from typing import List, Optional

def get_raw_question(db: Session, question_id: int) -> Optional[models.RawQuestion]:
    return db.query(models.RawQuestion).options(
        selectinload(models.RawQuestion.raw_answers.and_(models.RawAnswer.is_deleted == False)),
        selectinload(models.RawQuestion.expert_answers.and_(models.ExpertAnswer.is_deleted == False))
    ).filter(models.RawQuestion.id == question_id, models.RawQuestion.is_deleted == False).first()

def get_raw_question_including_deleted(db: Session, question_id: int) -> Optional[models.RawQuestion]:
    # Used for restore to get the item even if marked as deleted
    return db.query(models.RawQuestion).options(
        selectinload(models.RawQuestion.raw_answers), # Load all answers for restoration context
        selectinload(models.RawQuestion.expert_answers)
    ).filter(models.RawQuestion.id == question_id).first()


def get_raw_questions(db: Session, skip: int = 0, limit: int = 10) -> List[models.RawQuestion]:
    return db.query(models.RawQuestion).options(
        selectinload(models.RawQuestion.raw_answers.and_(models.RawAnswer.is_deleted == False)),
        selectinload(models.RawQuestion.expert_answers.and_(models.ExpertAnswer.is_deleted == False))
    ).filter(models.RawQuestion.is_deleted == False).order_by(models.RawQuestion.id.desc()).offset(skip).limit(limit).all()

# create_raw_question (deferred)

def set_raw_question_deleted_status(db: Session, question_id: int, deleted_status: bool) -> Optional[models.RawQuestion]:
    db_question = db.query(models.RawQuestion).filter(models.RawQuestion.id == question_id).first()
    if db_question:
        db_question.is_deleted = deleted_status
        # Note: Cascading soft delete for answers is handled by relationship cascade="all, delete-orphan"
        # if SQLAlchemy is configured for it, or manually:
        # if deleted_status:
        #     for ra in db_question.raw_answers: ra.is_deleted = True
        #     for ca in db_question.crowdsourced_answers: ca.is_deleted = True
        # Else, if restoring, answers might need separate restoration if they were individually deleted.
        # For simplicity, this example assumes deleting a question makes its answers effectively inaccessible
        # unless restored with the question or individually.
        db.commit()
        db.refresh(db_question)
        # For response, reload with filtered answers if it's a restore operation
        if not deleted_status:
             return get_raw_question(db, question_id) # Return with correctly filtered sub-items
        return db_question # For delete, the object state is fine
    return None

def set_multiple_raw_questions_deleted_status(db: Session, question_ids: List[int], deleted_status: bool) -> int:
    if not question_ids: 
        return 0
    num_updated = db.query(models.RawQuestion).filter(models.RawQuestion.id.in_(question_ids)).update({"is_deleted": deleted_status}, synchronize_session=False)
    db.commit()
    return num_updated