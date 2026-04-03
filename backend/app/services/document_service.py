import logging
import hashlib
import shutil
from pathlib import Path

from fastapi import UploadFile

from backend.app.models.domain import DocumentChunk, SavedUpload
from backend.app.repositories.document_metadata import DocumentMetadataRepository
from backend.app.services.document_loader import DocumentLoader
from backend.app.services.embedding import EmbeddingService
from backend.app.services.text_chunker import RecursiveTextChunker
from backend.app.services.vector_store import FaissVectorStore
from backend.app.storage.base import ObjectStorage


logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(
        self,
        upload_dir: Path,
        chunker: RecursiveTextChunker,
        loader: DocumentLoader,
        embedding_service: EmbeddingService,
        vector_store: FaissVectorStore,
        metadata_repository: DocumentMetadataRepository,
        object_storage: ObjectStorage,
    ) -> None:
        self.upload_dir = upload_dir
        self.chunker = chunker
        self.loader = loader
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.metadata_repository = metadata_repository
        self.object_storage = object_storage

    async def save_uploads_for_processing(self, workspace_id: str, files: list[UploadFile]) -> list[SavedUpload]:
        workspace_dir = self.upload_dir / workspace_id / "staging"
        workspace_dir.mkdir(parents=True, exist_ok=True)

        saved_uploads: list[SavedUpload] = []
        for index, file in enumerate(files, start=1):
            original_name = file.filename or f"uploaded_file_{index}"
            staging_path = workspace_dir / f"{index}_{original_name}"
            with staging_path.open("wb") as output_stream:
                shutil.copyfileobj(file.file, output_stream)
            file.file.close()
            saved_uploads.append(SavedUpload(original_name=original_name, staging_path=str(staging_path)))
        return saved_uploads

    def ingest_saved_uploads(self, workspace_id: str, uploads: list[SavedUpload]) -> tuple[list[str], int, list[str]]:
        document_ids: list[str] = []
        all_chunks: list[DocumentChunk] = []
        skipped_files: list[str] = []

        workspace_dir = self.upload_dir / workspace_id
        workspace_dir.mkdir(parents=True, exist_ok=True)

        try:
            for upload in uploads:
                original_name = upload.original_name
                temp_path = Path(upload.staging_path)
                checksum = hashlib.sha256()
                with temp_path.open("rb") as input_stream:
                    while True:
                        chunk = input_stream.read(1024 * 1024)
                        if not chunk:
                            break
                        checksum.update(chunk)

                file_checksum = checksum.hexdigest()
                existing_document = self.metadata_repository.get_by_checksum(workspace_id, file_checksum)
                if existing_document is not None:
                    temp_path.unlink(missing_ok=True)
                    skipped_files.append(original_name)
                    logger.info("Skipped duplicate file %s in workspace %s", original_name, workspace_id)
                    continue

                document_record = self.metadata_repository.create_document(
                    workspace_id=workspace_id,
                    file_name=original_name,
                    storage_path="",
                    checksum=file_checksum,
                    chunk_count=0,
                    status="processing",
                )

                object_key = f"{workspace_id}/{document_record.id}/v{document_record.version}/{original_name}"
                stored_path = self.object_storage.save_file(temp_path, object_key)

                document_ids.append(document_record.id)
                chunk_count = 0
                source_name = original_name
                processing_dir = self.upload_dir / workspace_id / "processing"
                local_processing_path = processing_dir / f"{document_record.id}_{original_name}"
                local_processing_path = self.object_storage.fetch_to_local(stored_path, local_processing_path)
                for page_number, page_text in self.loader.load(local_processing_path):
                    for text in self.chunker.split_text(page_text):
                        chunk_count += 1
                        chunk_id = f"{document_record.id}-chunk-{chunk_count}"
                        all_chunks.append(
                            DocumentChunk(
                                chunk_id=chunk_id,
                                document_id=document_record.id,
                                workspace_id=workspace_id,
                                text=text,
                                source_name=source_name,
                                page_number=page_number,
                            )
                        )

                document_record.storage_path = stored_path
                document_record.chunk_count = chunk_count
                document_record.status = "indexed"
                local_processing_path.unlink(missing_ok=True)

                logger.info("Indexed %s with %s chunks", original_name, chunk_count)

            embeddings = self.embedding_service.embed_texts([chunk.text for chunk in all_chunks]) if all_chunks else []
            if len(all_chunks) > 0:
                self.vector_store.upsert(workspace_id, embeddings, all_chunks)
            self.metadata_repository.session.commit()
            return document_ids, len(all_chunks), skipped_files
        except Exception:
            self.metadata_repository.session.rollback()
            raise
        finally:
            for upload in uploads:
                Path(upload.staging_path).unlink(missing_ok=True)

    def list_documents(self, workspace_id: str):
        return self.metadata_repository.list_workspace_documents(workspace_id)
