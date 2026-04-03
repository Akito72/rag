from backend.app.models.domain import ChatMessage
from backend.app.repositories.chat_history import ChatHistoryRepository


class ChatMemoryService:
    def __init__(self, repository: ChatHistoryRepository, max_messages: int) -> None:
        self.repository = repository
        self.max_messages = max_messages

    def append(self, workspace_id: str, session_id: str, role: str, content: str) -> None:
        self.repository.append_message(workspace_id, session_id, role, content)
        self.repository.session.commit()

    def append_many(self, workspace_id: str, session_id: str, messages: list[tuple[str, str]]) -> None:
        try:
            self.repository.append_messages(workspace_id, session_id, messages)
            self.repository.session.commit()
        except Exception:
            self.repository.session.rollback()
            raise

    def get(self, session_id: str) -> list[ChatMessage]:
        records = self.repository.get_messages(session_id, limit=self.max_messages)
        return [
            ChatMessage(role=record.role, content=record.content, created_at=record.created_at)
            for record in records
        ]
