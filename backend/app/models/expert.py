from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from ..db.database import Base

class Expert(Base):
    __tablename__ = "Expert"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    

    