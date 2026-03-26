from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)
    session_id: Optional[str] = "default"
    user_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = "default"
    user_id: Optional[str] = "default"