from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "production-rag"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    auto_create_schema: bool = True

    data_dir: Path = Path("./data")
    upload_dir: Path = Path("./data/uploads")
    index_dir: Path = Path("./data/indexes")
    metadata_path: Path = Path("./data/metadata.json")
    database_url: str = "sqlite:///./data/rag.db"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieval_top_k: int = 4
    max_chat_history_messages: int = 10

    openai_api_key: str | None = None
    openai_chat_model: str = "gpt-4o-mini"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    api_key: str | None = None
    object_storage_backend: str = "local"
    s3_bucket: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_default_region: str = "us-east-1"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    redis_url: str = "redis://redis:6379/2"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.index_dir.mkdir(parents=True, exist_ok=True)
