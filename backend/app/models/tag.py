from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from ..db.database import Base

class Tag(Base):
    __tablename__ = "Tag"

    label = Column(String(100), primary_key=True)
    
    # 多对多关系
    raw_questions = relationship("RawQuestion", secondary="RawQuestionTagRecords", back_populates="tags")
    std_questions = relationship("StdQuestion", secondary="QuestionTagRecords", back_populates="tags")

# 原始问题与标签的关联表
raw_question_tag_association = Table(
    'RawQuestionTagRecords',
    Base.metadata,
    Column('raw_question_id', Integer, ForeignKey('RawQuestion.id'), primary_key=True),
    Column('tag_label', String(100), ForeignKey('Tag.label'), primary_key=True)
)

# 标准问题与标签的关联表 (已存在于数据库schema中)
std_question_tag_association = Table(
    'QuestionTagRecords', 
    Base.metadata,
    Column('std_question_id', Integer, ForeignKey('StdQuestion.id'), primary_key=True),
    Column('tag_label', String(100), ForeignKey('Tag.label'), primary_key=True)
)
