from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.db import ChatMessageRecord, ChatSessionRecord, WorkspaceRecord


class ChatHistoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_workspace(self, workspace_id: str) -> WorkspaceRecord:
        workspace = self.session.get(WorkspaceRecord, workspace_id)
        if workspace is None:
            workspace = WorkspaceRecord(id=workspace_id)
            self.session.add(workspace)
            self.session.flush()
        return workspace

    def ensure_session(self, workspace_id: str, session_id: str) -> ChatSessionRecord:
        self.ensure_workspace(workspace_id)
        session_record = self.session.get(ChatSessionRecord, session_id)
        if session_record is None:
            session_record = ChatSessionRecord(id=session_id, workspace_id=workspace_id)
            self.session.add(session_record)
            self.session.flush()
        return session_record

    def append_message(self, workspace_id: str, session_id: str, role: str, content: str) -> ChatMessageRecord:
        self.ensure_session(workspace_id, session_id)
        message = ChatMessageRecord(session_id=session_id, role=role, content=content)
        self.session.add(message)
        self.session.flush()
        return message

    def append_messages(
        self,
        workspace_id: str,
        session_id: str,
        messages: list[tuple[str, str]],
    ) -> list[ChatMessageRecord]:
        self.ensure_session(workspace_id, session_id)
        records: list[ChatMessageRecord] = []
        for role, content in messages:
            record = ChatMessageRecord(session_id=session_id, role=role, content=content)
            self.session.add(record)
            records.append(record)
        self.session.flush()
        return records

    def get_messages(self, session_id: str, limit: int | None = None) -> list[ChatMessageRecord]:
        statement = (
            select(ChatMessageRecord)
            .where(ChatMessageRecord.session_id == session_id)
            .order_by(ChatMessageRecord.created_at.asc())
        )
        records = list(self.session.execute(statement).scalars().all())
        if limit is None or len(records) <= limit:
            return records
        return records[-limit:]
