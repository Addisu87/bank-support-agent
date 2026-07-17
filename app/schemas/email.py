from typing import Any, Dict

from pydantic import BaseModel, EmailStr


class EmailRequest(BaseModel):
    to_email: EmailStr
    template_type: str
    template_data: Dict[str, Any]
