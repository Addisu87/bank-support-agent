from sqlalchemy import (
    Column, String, DateTime, Boolean, JSON
    )
from app.db.models.base import BaseModel
from sqlalchemy.orm import relationship

class User(BaseModel):
    __tablename__ = "users"
    
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_pwd = Column(String(255), nullable=False)
    phone_number= Column(String(20))
    date_of_birth = Column(DateTime)
    address = Column(JSON)
    roles = Column(JSON, default=list)
    preferences = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True) 
    is_superuser = Column(Boolean, default=False)
    
    # Realtionships 
    accounts = relationship('Account', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
