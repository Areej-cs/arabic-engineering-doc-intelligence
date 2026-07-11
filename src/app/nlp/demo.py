"""Simple manual test: OCR-extract text from the sample report, then classify it."""

import sys

from loguru import logger

from src.app.nlp.classifier import load_encoder, load_head, predict
from src.app.ocr.extractor import extract_text
from src.app.ocr.sample_generator import DEFAULT_SAMPLE_PATH, generate_sample_image


def run_demo(sample_path=DEFAULT_SAMPLE_PATH) -> str:
    """Extract text from the OCR sample file, classify it, and print the result."""
    if not sample_path.exists():
        logger.info("Sample file not found, generating: {}", sample_path)
        generate_sample_image(sample_path)

    text = extract_text(sample_path)
    tokenizer, encoder = load_encoder()
    head = load_head()
    label = predict(text, tokenizer, encoder, head)

    print("--- OCR text ---")
    print(text)
    print("--- Predicted category ---")
    print(label)
    return label


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    run_demo()
