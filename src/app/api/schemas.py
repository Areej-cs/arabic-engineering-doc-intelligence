"""Request/response shapes for the API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    priority: str
    size_bytes: int
    created_at: datetime


class DocumentDetail(DocumentSummary):
    content_type: str | None
    storage_backend: str
    storage_key: str
    extracted_text: str


class DocumentList(BaseModel):
    total: int
    items: list[DocumentSummary]


class PriorityStats(BaseModel):
    total: int
    by_priority: dict[str, int]
