"""The full OCR -> classification pipeline, shared by the API and the dashboard."""

import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from src.app.core.config import get_settings
from src.app.nlp.classifier import load_encoder, load_head, predict
from src.app.ocr.extractor import extract_text

SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".pdf"}


@dataclass
class PipelineResult:
    text: str
    priority: str


@lru_cache(maxsize=1)
def get_classifier():
    """Load AraBERT + head once (slow to load)."""
    tokenizer, encoder = load_encoder()
    head = load_head()
    return tokenizer, encoder, head


def process_file(path: Path) -> PipelineResult:
    settings = get_settings()
    text = extract_text(path, lang=settings.tesseract_lang, engine=settings.ocr_engine)
    tokenizer, encoder, head = get_classifier()
    priority = predict(text, tokenizer, encoder, head)
    return PipelineResult(text=text, priority=priority)


def process_bytes(data: bytes, suffix: str) -> PipelineResult:
    """Same as process_file but for uploaded bytes (tesseract needs a real file)."""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    try:
        return process_file(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)
