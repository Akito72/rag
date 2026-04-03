from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    workspace_id: str
    text: str
    source_name: str
    page_number: int | None = None
    metadata: dict[str, str | int | float | None] = field(default_factory=dict)


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str
    created_at: datetime


@dataclass(slots=True)
class SavedUpload:
    original_name: str
    staging_path: str
