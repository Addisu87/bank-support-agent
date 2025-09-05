import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

# Base class for models
Base = declarative_base()

# 
class User(Base):
    __tablename__ = "users"
    
    id= Column(Integer, primary_key=True, index=True)
    full_name=Column(String(255), nullable=False, index=True)
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
    
    
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True)
    original_key = Column(String(1024))
    processed = Column(Boolean, default=False)
    extracted_text = Column(Text)
    thumbnail = Column(String(1024))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255))
    subject = Column(String(255))
    status = Column(String(50), default="open")
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer)
    sender = Column(String(255))
    body = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)