from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from ..crud import crud_raw_answer
from ..schemas import RawAnswer, Msg
from ..db.database import get_db

router = APIRouter(
    prefix="/api/raw_answers",
    tags=["Raw Answers"],
    responses={404: {"description": "Not found"}},
)

@router.delete("/{answer_id}/", response_model=Msg)
def delete_raw_answer_api(answer_id: int, db: Session = Depends(get_db)):
    db_answer = crud_raw_answer.set_raw_answer_deleted_status(db, answer_id=answer_id, deleted_status=True)
    if db_answer is None:
        raise HTTPException(status_code=404, detail="RawAnswer not found")
    return Msg(message=f"Raw answer {answer_id} marked as deleted")

@router.post("/{answer_id}/restore/", response_model=RawAnswer)
def restore_raw_answer_api(answer_id: int, db: Session = Depends(get_db)):
    initial_check = crud_raw_answer.get_raw_answer(db, answer_id=answer_id, include_deleted=True)
    if not initial_check:
         raise HTTPException(status_code=404, detail="RawAnswer not found")
    if not initial_check.is_deleted:
         raise HTTPException(status_code=400, detail="RawAnswer is not marked as deleted")

    db_answer = crud_raw_answer.set_raw_answer_deleted_status(db, answer_id=answer_id, deleted_status=False)
    if db_answer is None:
        raise HTTPException(status_code=404, detail="Error restoring RawAnswer")
    return db_answer

@router.post("/delete-multiple/", response_model=Msg)
def delete_multiple_raw_answers_api(answer_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    if not answer_ids:
        raise HTTPException(status_code=400, detail="No answer IDs provided")
    num_deleted = crud_raw_answer.set_multiple_raw_answers_deleted_status(db, answer_ids=answer_ids, deleted_status=True)
    return Msg(message=f"Successfully marked {num_deleted} raw answers as deleted")

@router.post("/restore-multiple/", response_model=Msg)
def restore_multiple_raw_answers_api(answer_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    if not answer_ids:
        raise HTTPException(status_code=400, detail="No answer IDs provided")
    num_restored = crud_raw_answer.set_multiple_raw_answers_deleted_status(db, answer_ids=answer_ids, deleted_status=False)
    return Msg(message=f"Successfully marked {num_restored} raw answers as not deleted")