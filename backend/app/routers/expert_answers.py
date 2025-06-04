from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from app.crud import crud_expert_answer
from app.schemas import ExpertAnswer, Msg
from app.db.database import get_db

router = APIRouter(
    prefix="/api/expert_answers",
    tags=["Expert Answers"],
    responses={404: {"description": "Not found"}},
)

@router.delete("/{answer_id}/", response_model=Msg)
def delete_expert_answer_api(answer_id: int, db: Session = Depends(get_db)):
    db_answer = crud_expert_answer.set_expert_answer_deleted_status(db, answer_id=answer_id, deleted_status=True)
    if db_answer is None:
        raise HTTPException(status_code=404, detail="ExpertAnswer not found")
    return Msg(message=f"Expert answer {answer_id} marked as deleted")

@router.post("/{answer_id}/restore/", response_model=ExpertAnswer)
def restore_expert_answer_api(answer_id: int, db: Session = Depends(get_db)):
    initial_check = crud_expert_answer.get_expert_answer(db, answer_id=answer_id, include_deleted=True)
    if not initial_check:
         raise HTTPException(status_code=404, detail="ExpertAnswer not found")
    if not initial_check.is_deleted:
         raise HTTPException(status_code=400, detail="ExpertAnswer is not marked as deleted")
    
    db_answer = crud_expert_answer.set_expert_answer_deleted_status(db, answer_id=answer_id, deleted_status=False)
    if db_answer is None:
        raise HTTPException(status_code=404, detail="Error restoring ExpertAnswer")
    return db_answer

@router.post("/delete-multiple/", response_model=Msg)
def delete_multiple_expert_answers_api(answer_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    if not answer_ids:
        raise HTTPException(status_code=400, detail="No answer IDs provided")
    num_deleted = crud_expert_answer.set_multiple_expert_answers_deleted_status(db, answer_ids=answer_ids, deleted_status=True)
    return Msg(message=f"Successfully marked {num_deleted} expert answers as deleted")

@router.post("/restore-multiple/", response_model=Msg)
def restore_multiple_expert_answers_api(answer_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    if not answer_ids:
        raise HTTPException(status_code=400, detail="No answer IDs provided")
    num_restored = crud_expert_answer.set_multiple_expert_answers_deleted_status(db, answer_ids=answer_ids, deleted_status=False)
    return Msg(message=f"Successfully marked {num_restored} expert answers as not deleted")