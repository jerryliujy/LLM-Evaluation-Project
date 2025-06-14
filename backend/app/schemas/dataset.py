from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class DatasetBase(BaseModel):
    name: str
    description: str
    is_public: bool = True
    version: int = 1

class DatasetCreate(DatasetBase):
    pass

class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    version: Optional[int] = None

class DatasetResponse(DatasetBase):
    id: int
    created_by: int  # 用户ID
    create_time: datetime
    version: int
    
    class Config:
        from_attributes = True

class DatasetWithStats(DatasetResponse):
    std_questions_count: int = 0
    std_answers_count: int = 0
    creator_username: Optional[str] = None  # 创建者用户名，用于显示
