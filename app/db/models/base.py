from sqlalchemy import (
    Column, Integer, DateTime, Boolean
    )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# Base class for models
Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_verified = Column(Boolean, default=False)