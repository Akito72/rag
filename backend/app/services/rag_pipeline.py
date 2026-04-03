from backend.app.schemas.chat import ChatResponse
from backend.app.services.chat_memory import ChatMemoryService
from backend.app.services.llm import LLMService
from backend.app.services.retriever import RetrieverService


class RAGPipeline:
    def __init__(
        self,
        retriever: RetrieverService,
        llm_service: LLMService,
        chat_memory: ChatMemoryService,
        default_top_k: int,
    ) -> None:
        self.retriever = retriever
        self.llm_service = llm_service
        self.chat_memory = chat_memory
        self.default_top_k = default_top_k

    def answer(self, workspace_id: str, session_id: str, question: str, top_k: int | None) -> ChatResponse:
        effective_top_k = top_k or self.default_top_k
        chat_history = self.chat_memory.get(session_id)
        sources = self.retriever.retrieve(workspace_id, question, effective_top_k)
        answer = self.llm_service.generate_answer(question=question, sources=sources, chat_history=chat_history)
        self.chat_memory.append_many(
            workspace_id,
            session_id,
            [("user", question), ("assistant", answer)],
        )
        return ChatResponse(session_id=session_id, answer=answer, sources=sources)
