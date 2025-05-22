from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from ..crud import crud_expert
from ..schemas import Expert, Msg
from ..db.database import get_db

router = APIRouter(
    prefix="/api/experts",
    tags=["Experts"],
    responses={404: {"description": "Not found"}},
)

@router.delete("/{expert_id}/", response_model=Msg)
def delete_expert_api(expert_id: int, db: Session = Depends(get_db)):
    db_answer = crud_expert.set_expert_deleted_status(db, expert_id=expert_id, deleted_status=True)
    if db_answer is None:
        raise HTTPException(status_code=404, detail="ExpertAnswer not found")
    return Msg(message=f"Expert {expert_id} marked as deleted")
