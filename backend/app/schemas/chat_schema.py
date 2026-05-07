from typing import Optional

from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str
    message: str


class ChatRequest(BaseModel):
    session_id: Optional[int] = None
    message: str = Field(..., min_length=1)
