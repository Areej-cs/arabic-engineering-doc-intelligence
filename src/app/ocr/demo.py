"""Simple manual test: run OCR extraction against one sample file."""

import sys
from pathlib import Path

from loguru import logger
from src.app.ocr.extractor import extract_text
from src.app.ocr.sample_generator import DEFAULT_SAMPLE_PATH, generate_sample_image


def run_demo(sample_path: Path = DEFAULT_SAMPLE_PATH) -> str:
    """Extract text from the sample file (generating it first if missing) and print it."""
    if not sample_path.exists():
        logger.info("Sample file not found, generating: {}", sample_path)
        generate_sample_image(sample_path)

    text = extract_text(sample_path)
    print("--- Extracted text ---")
    print(text)
    print("----------------------")
    return text


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    run_demo()
