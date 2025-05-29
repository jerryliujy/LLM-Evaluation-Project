from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class DatasetBase(BaseModel):
    description: str

class DatasetCreate(DatasetBase):
    pass

class DatasetUpdate(BaseModel):
    description: Optional[str] = None

class DatasetResponse(DatasetBase):
    id: int
    create_time: datetime
    
    class Config:
        from_attributes = True
