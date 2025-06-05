from pydantic import BaseModel
from typing import List, TypeVar, Generic

class Msg(BaseModel):
    message: str

# 泛型类型变量
T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
