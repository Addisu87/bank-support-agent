from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    use_cache: bool = Field(default=True)

class ChatResponse(BaseModel):
    response: str