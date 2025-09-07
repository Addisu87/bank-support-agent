import datetime
from sqlalchemy import (
    Column, Integer, String, JSON, DateTime, Text, ForeignKey, Float
    )
from sqlalchemy.orm import relationship, declarative_base

# Base class for models
Base = declarative_base()

# 
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    roles = Column(JSON, default=list)
    access_token = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    accounts = relationship("Account", back_populates="user")

class Audit(Base):
    __tablename__ = "audits"
    
    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(255))
    tool = Column(String(255))
    args = Column(Text)
    result = Column(Text)
    request_id = Column(String(255), index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Bank(Base):
    __tablename__ = "banks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    bic = Column(String(50), unique=True)
    country = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bank_id = Column(Integer, ForeignKey("banks.id"))
    account_number = Column(String(50), unique=True, nullable=False)
    balance = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    account_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="accounts")
    bank = relationship("Bank")
    transactions = relationship("Transaction", back_populates="account")
    cards = relationship("Card", back_populates="account")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    amount = Column(Float)
    currency = Column(String(10), default="USD")
    transaction_type = Column(String(50))
    description = Column(Text)
    merchant = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    account = relationship("Account", back_populates="transactions")

class Card(Base):
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    card_number = Column(String(20), unique=True, nullable=False)
    card_type = Column(String(50))
    status = Column(String(50), default="active")
    expiry_date = Column(DateTime)
    
    account = relationship("Account", back_populates="cards")
