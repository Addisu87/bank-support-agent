from pydantic import BaseModel, EmailStr
from typing import Dict, Any


class EmailRequest(BaseModel):
    to_email: EmailStr
    template_type: str
    template_data: Dict[str, Any]
