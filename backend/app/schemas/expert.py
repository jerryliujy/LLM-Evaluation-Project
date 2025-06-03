from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ExpertBase(BaseModel):
    name: str
    email: Optional[str] = None
    password: Optional[str] = None

class ExpertCreate(ExpertBase):
    pass

class ExpertLogin(BaseModel):
    email: str
    password: str

class ExpertLoginResponse(BaseModel):
    expert: 'Expert'
    access_token: Optional[str] = None
    token_type: Optional[str] = None

class Expert(ExpertBase):
    id: int
    created_at: datetime
    is_deleted: bool

    class Config:
        orm_mode = True

# 解决前向引用
ExpertLoginResponse.update_forward_refs()