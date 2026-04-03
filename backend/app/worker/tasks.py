from backend.app.worker.celery_app import celery_app
from backend.app.services.ingestion_service import run_ingestion_job


@celery_app.task(
    name="backend.app.worker.tasks.run_ingestion_job_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_ingestion_job_task(
    workspace_id: str,
    job_id: str,
    uploads: list[dict[str, str]],
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
    run_ingestion_job(
        workspace_id=workspace_id,
        job_id=job_id,
        uploads=uploads,
        upload_dir=upload_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        embedding_model=embedding_model,
        index_dir=index_dir,
        object_storage_backend=object_storage_backend,
        s3_bucket=s3_bucket,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_default_region=aws_default_region,
    )
