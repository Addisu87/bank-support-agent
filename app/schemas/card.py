from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.db.models.card import CardStatus, CardType


class CardBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    card_holder_name: str
    card_type: CardType
    daily_limit: float = 1000.0
    contactless_enabled: bool = True
    international_usage: bool = False


class CardCreate(CardBase):
    pass


class CardResponse(CardBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    bank_id: int
    card_number: str
    status: CardStatus
    expiry_date: datetime
    created_at: datetime
    updated_at: datetime | None


class CardUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    daily_limit: float | None = None
    contactless_enabled: bool | None = None
    international_usage: bool | None = None
    status: CardStatus | None = None


class CardSecurityUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current_cvv: str
    new_cvv: str

    @field_validator("new_cvv")
    def validate_cvv(cls, v):
        if len(v) != 3 or not v.isdigit():
            raise ValueError("CVV must be 3 digits")
        return v
