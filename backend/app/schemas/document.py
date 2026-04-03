from pydantic import BaseModel, Field


class SourceChunk(BaseModel):
    chunk_id: str
    document_id: str
    source_name: str
    text: str
    score: float
    page_number: int | None = None


class UploadResponse(BaseModel):
    workspace_id: str
    job_id: str
    document_ids: list[str] = Field(default_factory=list)
    chunk_count: int = 0
    skipped_files: list[str] = Field(default_factory=list)
    status: str = "pending"
    message: str = Field(default="Documents accepted for background indexing.")


class DocumentMetadataResponse(BaseModel):
    document_id: str
    workspace_id: str
    file_name: str
    storage_path: str
    checksum: str
    version: int
    chunk_count: int
    status: str
    created_at: str


class WorkspaceDocumentsResponse(BaseModel):
    workspace_id: str
    documents: list[DocumentMetadataResponse]


class IngestionJobResponse(BaseModel):
    job_id: str
    workspace_id: str
    status: str
    file_count: int
    chunk_count: int
    error_message: str | None = None
    created_at: str
    updated_at: str
