from functools import lru_cache

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.db import get_db_session
from backend.app.core.redis_client import get_redis_client
from backend.app.core.security import AuthContext
from backend.app.repositories.chat_history import ChatHistoryRepository
from backend.app.repositories.auth import AuthRepository
from backend.app.repositories.document_metadata import DocumentMetadataRepository
from backend.app.repositories.ingestion_jobs import IngestionJobRepository
from backend.app.services.auth import AuthService
from backend.app.services.chat_memory import ChatMemoryService
from backend.app.services.document_loader import DocumentLoader
from backend.app.services.document_service import DocumentService
from backend.app.services.embedding import EmbeddingService
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.llm import LLMService
from backend.app.services.rag_pipeline import RAGPipeline
from backend.app.services.retriever import RetrieverService
from backend.app.services.text_chunker import RecursiveTextChunker
from backend.app.services.vector_store import FaissVectorStore
from backend.app.storage.base import ObjectStorage
from backend.app.storage.local import LocalObjectStorage
from backend.app.storage.s3 import S3ObjectStorage


def get_document_metadata_repository(session: Session = Depends(get_db_session)) -> DocumentMetadataRepository:
    return DocumentMetadataRepository(session)


def get_auth_repository(session: Session = Depends(get_db_session)) -> AuthRepository:
    return AuthRepository(session)


def get_chat_history_repository(session: Session = Depends(get_db_session)) -> ChatHistoryRepository:
    return ChatHistoryRepository(session)


def get_ingestion_job_repository(session: Session = Depends(get_db_session)) -> IngestionJobRepository:
    return IngestionJobRepository(session)


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService(settings.embedding_model)


@lru_cache(maxsize=1)
def get_vector_store() -> FaissVectorStore:
    return FaissVectorStore(settings.index_dir)


@lru_cache(maxsize=1)
def get_object_storage() -> ObjectStorage:
    if settings.object_storage_backend.lower() == "s3":
        if not settings.s3_bucket:
            raise ValueError("S3 bucket must be configured when OBJECT_STORAGE_BACKEND=s3")
        return S3ObjectStorage(
            bucket=settings.s3_bucket,
            region=settings.aws_default_region,
            access_key_id=settings.aws_access_key_id,
            secret_access_key=settings.aws_secret_access_key,
        )
    return LocalObjectStorage(settings.upload_dir)


def get_auth_service(
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthService:
    return AuthService(
        repository=repository,
        jwt_secret_key=settings.jwt_secret_key,
        jwt_algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=settings.access_token_expire_minutes,
    )


def require_auth_context(
    auth_service: AuthService = Depends(get_auth_service),
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
) -> AuthContext:
    configured_key = settings.api_key
    if configured_key and x_api_key == configured_key:
        return AuthContext(user_id=None, workspace_ids=["*"], is_admin=True)

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")

    token = authorization.split(" ", maxsplit=1)[1]
    payload = auth_service.decode_token(token)
    return AuthContext(
        user_id=payload.get("sub"),
        workspace_ids=payload.get("workspace_ids", []),
        is_admin=False,
    )


def get_chat_memory(
    repository: ChatHistoryRepository = Depends(get_chat_history_repository),
) -> ChatMemoryService:
    return ChatMemoryService(repository, settings.max_chat_history_messages)


def get_document_service(
    repository: DocumentMetadataRepository = Depends(get_document_metadata_repository),
) -> DocumentService:
    return DocumentService(
        upload_dir=settings.upload_dir,
        chunker=RecursiveTextChunker(settings.chunk_size, settings.chunk_overlap),
        loader=DocumentLoader(),
        embedding_service=get_embedding_service(),
        vector_store=get_vector_store(),
        metadata_repository=repository,
        object_storage=get_object_storage(),
    )


def get_ingestion_service(
    document_service: DocumentService = Depends(get_document_service),
    repository: IngestionJobRepository = Depends(get_ingestion_job_repository),
) -> IngestionService:
    return IngestionService(document_service, repository)


def get_rag_pipeline(
    chat_memory: ChatMemoryService = Depends(get_chat_memory),
) -> RAGPipeline:
    retriever = RetrieverService(get_embedding_service(), get_vector_store())
    llm_service = LLMService(settings.openai_api_key, settings.openai_chat_model)
    return RAGPipeline(retriever, llm_service, chat_memory, settings.retrieval_top_k)
