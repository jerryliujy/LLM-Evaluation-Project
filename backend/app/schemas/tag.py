from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel

class TagBase(BaseModel):
    label: str


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    class Config:
        from_attributes = True


# 简化版本，避免循环导入
class TagWithQuestionsResponse(TagResponse):
    raw_questions_count: Optional[int] = 0
    std_questions_count: Optional[int] = 0

    class Config:
        from_attributes = True
