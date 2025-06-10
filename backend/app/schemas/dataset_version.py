from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DatasetVersionCreate(BaseModel):
    name: str
    description: Optional[str] = None

class DatasetVersionResponse(BaseModel):
    id: int
    dataset_id: int
    name: str
    description: Optional[str]
    version_number: str
    is_committed: bool
    is_public: bool
    created_by: int
    created_at: datetime
    committed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class DatasetVersionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class DatasetVersionPublish(BaseModel):
    is_public: bool = True  # 是否将版本标记为公开
