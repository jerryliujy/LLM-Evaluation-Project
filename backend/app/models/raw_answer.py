from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base

class RawAnswer(Base):
    __tablename__ = "Raw_Answer"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("Raw_Questions.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    vote_count = Column(Integer, default=0)
    author = Column(String(255), nullable=True)
    answered_at = Column(DateTime, nullable=True) 
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    question = relationship("RawQuestion", back_populates="RawAnswer")