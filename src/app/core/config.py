"""App settings (read from .env)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Arabic Engineering Document Intelligence"
    app_env: str = "development"
    debug: bool = False

    # ==== API ====
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: list[str] = ["http://localhost:8501"]
    max_upload_mb: int = 15

    # ==== Database ====
    # sqlite for quick local runs, postgres in docker-compose
    database_url: str = "sqlite+aiosqlite:///./local.db"

    # ==== Storage ====
    storage_backend: str = "local"  # local | s3
    local_storage_dir: Path = PROJECT_ROOT / "data" / "uploads"
    aws_region: str = "me-south-1"
    s3_bucket_name: str = "arabic-eng-doc-intelligence"
    s3_endpoint_url: str | None = None  # only needed for MinIO etc.

    # ==== OCR ====
    ocr_engine: str = "tesseract"  # tesseract | easyocr
    tesseract_lang: str = "ara+eng"


@lru_cache
def get_settings() -> Settings:
    return Settings()
