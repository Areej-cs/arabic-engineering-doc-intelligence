"""/documents endpoints: upload a report, list processed reports, fetch one, stats."""

import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.api.schemas import DocumentDetail, DocumentList, PriorityStats
from src.app.core.config import get_settings
from src.app.db.models import Document
from src.app.db.session import get_session
from src.app.nlp.classifier import LABELS
from src.app.services.pipeline import SUPPORTED_SUFFIXES, PipelineResult, process_bytes
from src.app.storage.storage import Storage, get_storage
from starlette.concurrency import run_in_threadpool

router = APIRouter(prefix="/documents", tags=["documents"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_storage_dep() -> Storage:
    return get_storage()


def get_processor() -> Callable[[bytes, str], PipelineResult]:
    return process_bytes


StorageDep = Annotated[Storage, Depends(get_storage_dep)]
ProcessorDep = Annotated[Callable[[bytes, str], PipelineResult], Depends(get_processor)]


@router.post("", response_model=DocumentDetail, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile, session: SessionDep, storage: StorageDep, processor: ProcessorDep
) -> Document:
    """Upload a report -> OCR + classify -> save file and result."""
    filename = Path(file.filename or "upload").name
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"unsupported file type '{suffix}', expected one of {sorted(SUPPORTED_SUFFIXES)}",
        )

    data = await file.read()
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "empty file")
    if len(data) > max_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "file too large")

    # OCR + model are blocking, run in a thread so the API doesn't freeze
    try:
        result = await run_in_threadpool(processor, data, suffix)
    except Exception as e:
        logger.exception("processing failed for {}", filename)
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"could not process file: {e}"
        ) from e

    doc_id = str(uuid.uuid4())
    key = f"documents/{doc_id}{suffix}"
    await run_in_threadpool(storage.save, key, data, file.content_type)

    doc = Document(
        id=doc_id,
        filename=filename,
        content_type=file.content_type,
        size_bytes=len(data),
        storage_backend=storage.name,
        storage_key=key,
        extracted_text=result.text,
        priority=result.priority,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    logger.info("processed {} -> {} ({})", filename, doc.priority, doc.id)
    return doc


@router.get("", response_model=DocumentList)
async def list_documents(
    session: SessionDep,
    priority: Annotated[str | None, Query(description="Filter: Urgent / Normal / Low")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DocumentList:
    """Newest first, optional priority filter."""
    if priority is not None and priority not in LABELS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"priority must be one of {LABELS}")

    query = select(Document)
    count_query = select(func.count()).select_from(Document)
    if priority:
        query = query.where(Document.priority == priority)
        count_query = count_query.where(Document.priority == priority)

    total = (await session.execute(count_query)).scalar_one()
    rows = await session.execute(
        query.order_by(Document.created_at.desc()).limit(limit).offset(offset)
    )
    return DocumentList(total=total, items=list(rows.scalars()))


@router.get("/stats", response_model=PriorityStats)
async def document_stats(session: SessionDep) -> PriorityStats:
    """Count of reports per priority."""
    rows = await session.execute(
        select(Document.priority, func.count()).group_by(Document.priority)
    )
    counts = {label: 0 for label in LABELS}
    counts.update({p: c for p, c in rows.all()})
    return PriorityStats(total=sum(counts.values()), by_priority=counts)


async def _get_or_404(session: AsyncSession, document_id: str) -> Document:
    doc = await session.get(Document, document_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "document not found")
    return doc


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(document_id: str, session: SessionDep) -> Document:
    return await _get_or_404(session, document_id)


@router.get("/{document_id}/file")
async def download_original(document_id: str, session: SessionDep, storage: StorageDep) -> Response:
    """Download the original uploaded file."""
    doc = await _get_or_404(session, document_id)
    data = await run_in_threadpool(storage.load, doc.storage_key)
    download_name = f"{doc.id}{Path(doc.filename).suffix}"
    return Response(
        content=data,
        media_type=doc.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )
