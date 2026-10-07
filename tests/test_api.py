"""Tests for the API.

OCR/AraBERT are replaced by a fake processor and the DB is a temp sqlite file, so this
runs without tesseract, the model or postgres.
"""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from src.app.api.main import app
from src.app.api.routes.documents import get_processor, get_storage_dep
from src.app.db.models import Base
from src.app.db.session import get_session
from src.app.services.pipeline import PipelineResult
from src.app.storage.storage import LocalStorage


def fake_processor(data: bytes, suffix: str) -> PipelineResult:
    # uploaded bytes = "ocr text", urgent if it mentions a leak
    text = data.decode("utf-8", errors="ignore")
    priority = "Urgent" if "تسرب" in text else "Normal"
    return PipelineResult(text=text, priority=priority)


@pytest.fixture
async def client(tmp_path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session():
        async with session_factory() as session:
            yield session

    storage = LocalStorage(tmp_path / "uploads")
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_storage_dep] = lambda: storage
    app.dependency_overrides[get_processor] = lambda: fake_processor

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    await engine.dispose()


async def _upload(client: AsyncClient, text: str, name: str = "report.png"):
    return await client.post(
        "/api/v1/documents",
        files={"file": (name, text.encode("utf-8"), "image/png")},
    )


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_upload_processes_stores_and_returns_document(client: AsyncClient) -> None:
    response = await _upload(client, "تسرب زيت في المضخة P-101")

    assert response.status_code == 201
    body = response.json()
    assert body["priority"] == "Urgent"
    assert body["filename"] == "report.png"
    assert body["storage_backend"] == "local"
    assert "تسرب" in body["extracted_text"]

    original = await client.get(f"/api/v1/documents/{body['id']}/file")
    assert original.status_code == 200
    assert original.content.decode("utf-8") == "تسرب زيت في المضخة P-101"


async def test_upload_rejects_unsupported_type(client: AsyncClient) -> None:
    response = await _upload(client, "hello", name="report.docx")
    assert response.status_code == 415


async def test_upload_rejects_empty_file(client: AsyncClient) -> None:
    response = await _upload(client, "")
    assert response.status_code == 400


async def test_list_filters_by_priority_and_stats_count(client: AsyncClient) -> None:
    await _upload(client, "تسرب غاز")
    await _upload(client, "فحص دوري")
    await _upload(client, "فحص دوري ثاني")

    urgent = (await client.get("/api/v1/documents", params={"priority": "Urgent"})).json()
    assert urgent["total"] == 1
    assert urgent["items"][0]["priority"] == "Urgent"

    everything = (await client.get("/api/v1/documents")).json()
    assert everything["total"] == 3

    stats = (await client.get("/api/v1/documents/stats")).json()
    assert stats == {"total": 3, "by_priority": {"Urgent": 1, "Normal": 2, "Low": 0}}


async def test_list_rejects_unknown_priority(client: AsyncClient) -> None:
    response = await client.get("/api/v1/documents", params={"priority": "Critical"})
    assert response.status_code == 400


async def test_get_missing_document_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/documents/does-not-exist")
    assert response.status_code == 404
