from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.db import IngestionJobRecord, WorkspaceRecord


class IngestionJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_workspace(self, workspace_id: str) -> WorkspaceRecord:
        workspace = self.session.get(WorkspaceRecord, workspace_id)
        if workspace is None:
            workspace = WorkspaceRecord(id=workspace_id)
            self.session.add(workspace)
            self.session.flush()
        return workspace

    def create_job(self, workspace_id: str, file_count: int) -> IngestionJobRecord:
        self.ensure_workspace(workspace_id)
        job = IngestionJobRecord(workspace_id=workspace_id, file_count=file_count, status="pending")
        self.session.add(job)
        self.session.flush()
        return job

    def get_job(self, job_id: str) -> IngestionJobRecord | None:
        return self.session.get(IngestionJobRecord, job_id)

    def list_jobs(self, workspace_id: str) -> list[IngestionJobRecord]:
        statement = (
            select(IngestionJobRecord)
            .where(IngestionJobRecord.workspace_id == workspace_id)
            .order_by(IngestionJobRecord.created_at.desc())
        )
        return list(self.session.execute(statement).scalars().all())
