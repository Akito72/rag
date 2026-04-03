from pathlib import Path

import boto3

from backend.app.storage.base import ObjectStorage


class S3ObjectStorage(ObjectStorage):
    def __init__(
        self,
        bucket: str,
        region: str,
        access_key_id: str | None,
        secret_access_key: str | None,
    ) -> None:
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    def save_file(self, source_path: Path, destination_key: str) -> str:
        self.client.upload_file(str(source_path), self.bucket, destination_key)
        source_path.unlink(missing_ok=True)
        return f"s3://{self.bucket}/{destination_key}"

    def fetch_to_local(self, storage_path: str, local_path: Path) -> Path:
        prefix = f"s3://{self.bucket}/"
        if not storage_path.startswith(prefix):
            raise ValueError("Storage path does not match configured S3 bucket.")
        object_key = storage_path.removeprefix(prefix)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(self.bucket, object_key, str(local_path))
        return local_path
