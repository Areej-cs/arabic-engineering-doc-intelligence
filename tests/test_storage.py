"""Tests for storage backends (S3 uses moto, no real AWS)."""

from pathlib import Path

import boto3
import pytest
from moto import mock_aws
from src.app.core.config import Settings
from src.app.storage.storage import LocalStorage, S3Storage, get_storage


def test_local_storage_round_trip(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    storage.save("documents/a.png", b"abc")
    assert storage.load("documents/a.png") == b"abc"


def test_local_storage_blocks_path_traversal(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path / "uploads")
    with pytest.raises(ValueError):
        storage.save("../outside.txt", b"nope")


@mock_aws
def test_s3_storage_round_trip() -> None:
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="test-bucket")
    storage = S3Storage("test-bucket", "us-east-1", client=client)

    storage.save("documents/a.pdf", b"%PDF-1.4", content_type="application/pdf")

    assert storage.load("documents/a.pdf") == b"%PDF-1.4"
    head = client.head_object(Bucket="test-bucket", Key="documents/a.pdf")
    assert head["ContentType"] == "application/pdf"


def test_get_storage_picks_backend_from_settings(tmp_path: Path) -> None:
    local = get_storage(Settings(storage_backend="local", local_storage_dir=tmp_path))
    assert isinstance(local, LocalStorage)

    with pytest.raises(ValueError):
        get_storage(Settings(storage_backend="ftp"))
