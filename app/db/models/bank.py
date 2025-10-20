from sqlalchemy import (
    Column, String, Text, Boolean
    )
from sqlalchemy.orm import relationship
from app.db.models.base import BaseModel

class Bank(BaseModel):
    __tablename__ = "banks"
    
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False) #Bank code -CBE
    swift_code = Column(String(11), unique=True) # SWIFT/BIC code
    routing_number = Column(String(9))
    country = Column(String(100), nullable=False)
    currency = Column(String(3), default='USD')
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    website = Column(String(255))
    address = Column(Text)
    is_active = Column(Boolean, default=True)
    
    accounts = relationship("Account", back_populates="bank", cascade="all, delete-orphan")
    issued_cards = relationship('Card', back_populates='issuing_bank')
    
    def __repr__(self):
        return f"<Bank(id={self.id}, name={self.name}, code={self.code})>"