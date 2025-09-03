# Pydantic schemas for agent outputs
from pydantic import BaseModel
from typing import List

class SupportResponse(BaseModel):
    answer: str | None = None
    balance: str | None = None
    status: str | None = None
    escalation_required: bool = False
    details: List[str] | None = None