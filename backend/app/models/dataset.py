from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.sql import func
from ..db.database import Base

class Dataset(Base):
    __tablename__ = "Dataset"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    create_time = Column(DateTime(timezone=True), server_default=func.now())
