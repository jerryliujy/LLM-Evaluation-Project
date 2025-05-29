from typing import List, Optional
from pydantic import BaseModel


class TagBase(BaseModel):
    label: str


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    class Config:
        from_attributes = True


class TagWithQuestionsResponse(TagResponse):
    raw_questions: Optional[List["RawQuestionResponse"]] = []
    std_questions: Optional[List["StdQuestionResponse"]] = []

    class Config:
        from_attributes = True


# 防止循环导入，在需要时再导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .raw_question import RawQuestionResponse
    from .std_question import StdQuestionResponse
