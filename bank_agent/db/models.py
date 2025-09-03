import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

# Base class for models
Base = declarative_base()

# 
class User(Base):
    __tablename__ = "users"
    
    id= Column(Integer, primary_key=True, index=True)
    name=Column(String(255), nullable=False, index=True)
    email= Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    roles = Column(JSON, default=list)
    access_token = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    
class Audit(Base):
    
    __tablename__ = "audits"
    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(255))
    tool = Column(String(255))
    args = Column(Text)
    result = Column(Text)
    request_id = Column(String(255), index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)