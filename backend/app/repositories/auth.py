from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.db import UserRecord, WorkspaceMembershipRecord, WorkspaceRecord


class AuthRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_user_by_email(self, email: str) -> UserRecord | None:
        statement = select(UserRecord).where(UserRecord.email == email)
        return self.session.execute(statement).scalar_one_or_none()

    def get_user_by_id(self, user_id: str) -> UserRecord | None:
        return self.session.get(UserRecord, user_id)

    def ensure_workspace(self, workspace_id: str) -> WorkspaceRecord:
        workspace = self.session.get(WorkspaceRecord, workspace_id)
        if workspace is None:
            workspace = WorkspaceRecord(id=workspace_id)
            self.session.add(workspace)
            self.session.flush()
        return workspace

    def create_user(self, email: str, password_hash: str) -> UserRecord:
        user = UserRecord(email=email, password_hash=password_hash)
        self.session.add(user)
        self.session.flush()
        return user

    def add_user_to_workspace(self, user_id: str, workspace_id: str, role: str = "owner") -> WorkspaceMembershipRecord:
        self.ensure_workspace(workspace_id)
        membership = WorkspaceMembershipRecord(user_id=user_id, workspace_id=workspace_id, role=role)
        self.session.add(membership)
        self.session.flush()
        return membership

    def list_workspace_ids_for_user(self, user_id: str) -> list[str]:
        statement = select(WorkspaceMembershipRecord.workspace_id).where(WorkspaceMembershipRecord.user_id == user_id)
        return list(self.session.execute(statement).scalars().all())
