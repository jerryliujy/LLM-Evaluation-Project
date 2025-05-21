from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base

class ExpertAnswer(Base):
    __tablename__ = "Expert_Answer"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("Raw_Question.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=False, index=True)
    vote_count = Column(Integer, default=0, nullable=True)
    author = Column(Integer, ForeignKey("Expert.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())   
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    question = relationship("RawQuestion", back_populates="ExpertAnswer")