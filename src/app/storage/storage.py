"""Storage for uploaded files: local disk for development, S3 for production.

Picked with STORAGE_BACKEND in .env.
"""

from pathlib import Path
from typing import Protocol

from src.app.core.config import Settings, get_settings


class Storage(Protocol):
    name: str

    def save(self, key: str, data: bytes, content_type: str | None = None) -> str: ...

    def load(self, key: str) -> bytes: ...


class LocalStorage:
    name = "local"

    def __init__(self, root: Path):
        self.root = Path(root)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root.resolve() not in path.parents:
            raise ValueError(f"invalid storage key: {key}")
        return path

    def save(self, key: str, data: bytes, content_type: str | None = None) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def load(self, key: str) -> bytes:
        return self._path(key).read_bytes()


class S3Storage:
    name = "s3"

    def __init__(self, bucket: str, region: str, endpoint_url: str | None = None, client=None):
        if client is None:
            import boto3

            # on EC2 boto3 uses the instance IAM role, so no keys needed
            client = boto3.client("s3", region_name=region, endpoint_url=endpoint_url)
        self.client = client
        self.bucket = bucket

    def save(self, key: str, data: bytes, content_type: str | None = None) -> str:
        extra = {"ContentType": content_type} if content_type else {}
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, **extra)
        return key

    def load(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()


def get_storage(settings: Settings | None = None) -> Storage:
    settings = settings or get_settings()
    if settings.storage_backend == "s3":
        return S3Storage(settings.s3_bucket_name, settings.aws_region, settings.s3_endpoint_url)
    if settings.storage_backend == "local":
        return LocalStorage(settings.local_storage_dir)
    raise ValueError(f"unknown STORAGE_BACKEND: {settings.storage_backend}")
