from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ExpertBase(BaseModel):
    name: str
    type: str

class ExpertCreate(ExpertBase):
    pass

class Expert(ExpertBase):
    id: int
    created_at: datetime
    is_active: bool
    is_deleted: bool

    class Config:
        orm_mode = True