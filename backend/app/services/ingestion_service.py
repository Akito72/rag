import logging
from dataclasses import asdict
from pathlib import Path

from backend.app.core.db import SessionLocal
from backend.app.models.domain import SavedUpload
from backend.app.repositories.document_metadata import DocumentMetadataRepository
from backend.app.repositories.ingestion_jobs import IngestionJobRepository
from backend.app.services.document_loader import DocumentLoader
from backend.app.services.document_service import DocumentService
from backend.app.services.embedding import EmbeddingService
from backend.app.services.text_chunker import RecursiveTextChunker
from backend.app.services.vector_store import FaissVectorStore
from backend.app.storage.base import ObjectStorage
from backend.app.storage.local import LocalObjectStorage
from backend.app.storage.s3 import S3ObjectStorage


logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
        self,
        document_service: DocumentService,
        job_repository: IngestionJobRepository,
    ) -> None:
        self.document_service = document_service
        self.job_repository = job_repository

    def create_job(self, workspace_id: str, file_count: int) -> str:
        job = self.job_repository.create_job(workspace_id, file_count)
        self.job_repository.session.commit()
        return job.id

    def get_job(self, job_id: str):
        return self.job_repository.get_job(job_id)

    def list_jobs(self, workspace_id: str):
        return self.job_repository.list_jobs(workspace_id)

    def enqueue_job(
        self,
        workspace_id: str,
        job_id: str,
        uploads: list[SavedUpload],
        upload_dir: str,
        chunk_size: int,
        chunk_overlap: int,
        embedding_model: str,
        index_dir: str,
        object_storage_backend: str,
        s3_bucket: str | None,
        aws_access_key_id: str | None,
        aws_secret_access_key: str | None,
        aws_default_region: str,
    ) -> None:
        from backend.app.worker.tasks import run_ingestion_job_task

        serialized_uploads = [asdict(upload) for upload in uploads]
        run_ingestion_job_task.delay(
            workspace_id,
            job_id,
            serialized_uploads,
            upload_dir,
            chunk_size,
            chunk_overlap,
            embedding_model,
            index_dir,
            object_storage_backend,
            s3_bucket,
            aws_access_key_id,
            aws_secret_access_key,
            aws_default_region,
        )


def run_ingestion_job(
    workspace_id: str,
    job_id: str,
    uploads: list[SavedUpload] | list[dict[str, str]],
    upload_dir: str,
    chunk_size: int,
    chunk_overlap: int,
    embedding_model: str,
    index_dir: str,
    object_storage_backend: str,
    s3_bucket: str | None,
    aws_access_key_id: str | None,
    aws_secret_access_key: str | None,
    aws_default_region: str,
) -> None:
    normalized_uploads = [
        upload if isinstance(upload, SavedUpload) else SavedUpload(**upload)
        for upload in uploads
    ]
    session = SessionLocal()
    job_repository = IngestionJobRepository(session)
    metadata_repository = DocumentMetadataRepository(session)
    embedding_service = EmbeddingService(embedding_model)
    object_storage: ObjectStorage
    if object_storage_backend.lower() == "s3":
        if not s3_bucket:
            raise ValueError("S3 bucket must be configured when OBJECT_STORAGE_BACKEND=s3")
        object_storage = S3ObjectStorage(
            bucket=s3_bucket,
            region=aws_default_region,
            access_key_id=aws_access_key_id,
            secret_access_key=aws_secret_access_key,
        )
    else:
        object_storage = LocalObjectStorage(Path(upload_dir))

    document_service = DocumentService(
        upload_dir=Path(upload_dir),
        chunker=RecursiveTextChunker(chunk_size, chunk_overlap),
        loader=DocumentLoader(),
        embedding_service=embedding_service,
        vector_store=FaissVectorStore(Path(index_dir)),
        metadata_repository=metadata_repository,
        object_storage=object_storage,
    )

    job = job_repository.get_job(job_id)
    if job is None:
        session.close()
        return

    try:
        job.status = "processing"
        session.commit()

        document_ids, chunk_count, skipped_files = document_service.ingest_saved_uploads(workspace_id, normalized_uploads)
        job.status = "completed"
        job.chunk_count = chunk_count
        if skipped_files and len(skipped_files) == job.file_count:
            job.status = "skipped"
        session.commit()
        logger.info("Completed ingestion job %s with %s documents", job_id, len(document_ids))
    except Exception as exc:
        session.rollback()
        failed_job = job_repository.get_job(job_id)
        if failed_job is not None:
            failed_job.status = "failed"
            failed_job.error_message = str(exc)
            session.commit()
        logger.exception("Background ingestion job %s failed.", job_id)
    finally:
        session.close()
