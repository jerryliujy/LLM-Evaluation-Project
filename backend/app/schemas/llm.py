from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class LLMBase(BaseModel):
    name: str
    display_name: str
    provider: str
    api_endpoint: Optional[str] = None
    default_temperature: Optional[Decimal] = Decimal("0.7")
    max_tokens: Optional[int] = 4000
    top_k: Optional[int] = 50
    enable_reasoning: bool = False
    cost_per_1k_tokens: Optional[Decimal] = Decimal("0.0006")
    description: Optional[str] = None
    version: Optional[str] = None
    affiliation: Optional[str] = None
    is_active: bool = True

class LLMCreate(LLMBase):
    pass

class LLMUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    provider: Optional[str] = None
    api_endpoint: Optional[str] = None
    default_temperature: Optional[Decimal] = None
    max_tokens: Optional[int] = None
    top_k: Optional[int] = None
    enable_reasoning: Optional[bool] = None
    cost_per_1k_tokens: Optional[Decimal] = None
    description: Optional[str] = None
    version: Optional[str] = None
    affiliation: Optional[str] = None
    is_active: Optional[bool] = None

class LLM(LLMBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
