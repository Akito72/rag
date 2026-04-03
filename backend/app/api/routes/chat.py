import logging

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.deps import get_chat_memory, get_rag_pipeline, require_auth_context
from backend.app.core.security import AuthContext, enforce_workspace_access
from backend.app.schemas.chat import ChatHistoryMessage, ChatHistoryResponse, ChatRequest, ChatResponse
from backend.app.services.chat_memory import ChatMemoryService
from backend.app.services.rag_pipeline import RAGPipeline


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=ChatResponse)
def query_documents(
    payload: ChatRequest,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
    auth_context: AuthContext = Depends(require_auth_context),
) -> ChatResponse:
    try:
        enforce_workspace_access(auth_context, payload.workspace_id)
        return rag_pipeline.answer(
            workspace_id=payload.workspace_id,
            session_id=payload.session_id,
            question=payload.question,
            top_k=payload.top_k,
        )
    except Exception as exc:
        logger.exception("Chat query failed.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to answer query.") from exc


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
def get_chat_history(
    session_id: str,
    workspace_id: str,
    chat_memory: ChatMemoryService = Depends(get_chat_memory),
    auth_context: AuthContext = Depends(require_auth_context),
) -> ChatHistoryResponse:
    enforce_workspace_access(auth_context, workspace_id)
    messages = [
        ChatHistoryMessage(
            role=message.role,
            content=message.content,
            created_at=message.created_at.isoformat(),
        )
        for message in chat_memory.get(session_id)
    ]
    return ChatHistoryResponse(session_id=session_id, messages=messages)
