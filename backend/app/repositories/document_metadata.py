from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.db import DocumentRecord, WorkspaceRecord


class DocumentMetadataRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_workspace(self, workspace_id: str) -> WorkspaceRecord:
        workspace = self.session.get(WorkspaceRecord, workspace_id)
        if workspace is None:
            workspace = WorkspaceRecord(id=workspace_id)
            self.session.add(workspace)
            self.session.flush()
        return workspace

    def get_by_checksum(self, workspace_id: str, checksum: str) -> DocumentRecord | None:
        statement = select(DocumentRecord).where(
            DocumentRecord.workspace_id == workspace_id,
            DocumentRecord.checksum == checksum,
        )
        return self.session.execute(statement).scalar_one_or_none()

    def get_next_version(self, workspace_id: str, file_name: str) -> int:
        statement = select(DocumentRecord).where(
            DocumentRecord.workspace_id == workspace_id,
            DocumentRecord.file_name == file_name,
        )
        records = self.session.execute(statement).scalars().all()
        if not records:
            return 1
        return max(record.version for record in records) + 1

    def create_document(
        self,
        workspace_id: str,
        file_name: str,
        storage_path: str,
        checksum: str,
        chunk_count: int,
        status: str = "indexed",
    ) -> DocumentRecord:
        self.ensure_workspace(workspace_id)
        record = DocumentRecord(
            workspace_id=workspace_id,
            file_name=file_name,
            storage_path=storage_path,
            checksum=checksum,
            version=self.get_next_version(workspace_id, file_name),
            chunk_count=chunk_count,
            status=status,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def list_workspace_documents(self, workspace_id: str) -> list[DocumentRecord]:
        statement = (
            select(DocumentRecord)
            .where(DocumentRecord.workspace_id == workspace_id)
            .order_by(DocumentRecord.created_at.desc())
        )
        return list(self.session.execute(statement).scalars().all())
