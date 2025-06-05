from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ExpertTaskBase(BaseModel):
    invite_code: str
    task_name: Optional[str] = None
    description: Optional[str] = None

class ExpertTaskCreate(ExpertTaskBase):
    pass

class ExpertTaskUpdate(BaseModel):
    task_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ExpertTask(ExpertTaskBase):
    id: int
    expert_id: int
    admin_id: int
    created_at: datetime
    is_active: bool
    
    # 关联信息
    expert_username: Optional[str] = None
    admin_username: Optional[str] = None

    class Config:
        from_attributes = True

class InviteCodeRequest(BaseModel):
    invite_code: str
