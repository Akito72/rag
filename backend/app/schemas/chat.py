from pydantic import BaseModel, Field

from backend.app.schemas.document import SourceChunk


class ChatRequest(BaseModel):
    workspace_id: str
    session_id: str
    question: str = Field(min_length=3)
    top_k: int | None = Field(default=None, ge=1, le=20)


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceChunk]


class ChatHistoryMessage(BaseModel):
    role: str
    content: str
    created_at: str


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatHistoryMessage]
