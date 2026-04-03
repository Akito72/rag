import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.app.api.deps import get_document_service, get_ingestion_service, require_auth_context
from backend.app.core.config import settings
from backend.app.core.security import AuthContext, enforce_workspace_access
from backend.app.schemas.document import (
    DocumentMetadataResponse,
    IngestionJobResponse,
    UploadResponse,
    WorkspaceDocumentsResponse,
)
from backend.app.services.document_service import DocumentService
from backend.app.services.ingestion_service import IngestionService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_documents(
    workspace_id: str = Form(...),
    files: list[UploadFile] = File(...),
    document_service: DocumentService = Depends(get_document_service),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
    auth_context: AuthContext = Depends(require_auth_context),
) -> UploadResponse:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one file is required.")
    enforce_workspace_access(auth_context, workspace_id)

    try:
        saved_uploads = await document_service.save_uploads_for_processing(workspace_id, files)
        job_id = ingestion_service.create_job(workspace_id, len(saved_uploads))
        ingestion_service.enqueue_job(
            workspace_id,
            job_id,
            saved_uploads,
            str(settings.upload_dir),
            settings.chunk_size,
            settings.chunk_overlap,
            settings.embedding_model,
            str(settings.index_dir),
            settings.object_storage_backend,
            settings.s3_bucket,
            settings.aws_access_key_id,
            settings.aws_secret_access_key,
            settings.aws_default_region,
        )
    except ValueError as exc:
        logger.exception("Document validation failed.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Document ingestion failed.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload documents.") from exc

    return UploadResponse(
        workspace_id=workspace_id,
        job_id=job_id,
        status="pending",
    )


@router.get("/{workspace_id}", response_model=WorkspaceDocumentsResponse)
def list_workspace_documents(
    workspace_id: str,
    document_service: DocumentService = Depends(get_document_service),
    auth_context: AuthContext = Depends(require_auth_context),
) -> WorkspaceDocumentsResponse:
    enforce_workspace_access(auth_context, workspace_id)
    records = document_service.list_documents(workspace_id)
    return WorkspaceDocumentsResponse(
        workspace_id=workspace_id,
        documents=[
            DocumentMetadataResponse(
                document_id=record.id,
                workspace_id=record.workspace_id,
                file_name=record.file_name,
                storage_path=record.storage_path,
                checksum=record.checksum,
                version=record.version,
                chunk_count=record.chunk_count,
                status=record.status,
                created_at=record.created_at.isoformat(),
            )
            for record in records
        ],
    )


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
def get_ingestion_job(
    job_id: str,
    ingestion_service: IngestionService = Depends(get_ingestion_service),
    auth_context: AuthContext = Depends(require_auth_context),
) -> IngestionJobResponse:
    job = ingestion_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    enforce_workspace_access(auth_context, job.workspace_id)

    return IngestionJobResponse(
        job_id=job.id,
        workspace_id=job.workspace_id,
        status=job.status,
        file_count=job.file_count,
        chunk_count=job.chunk_count,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
    )
