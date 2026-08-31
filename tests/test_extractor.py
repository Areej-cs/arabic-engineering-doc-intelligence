"""Tests for src.app.ocr.extractor.

The actual OCR call (pytesseract/cv2) is mocked out here - these tests check
the routing and validation logic in this module, not OCR accuracy, so they
run without a local Tesseract install.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image
from src.app.ocr.extractor import extract_text, extract_text_from_image


def test_extract_text_missing_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.png"
    with pytest.raises(FileNotFoundError):
        extract_text(missing)


def test_extract_text_unsupported_extension_raises(tmp_path: Path) -> None:
    unsupported = tmp_path / "report.docx"
    unsupported.write_text("not really a docx")
    with pytest.raises(ValueError):
        extract_text(unsupported)


def test_extract_text_routes_images_to_image_extractor(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    Image.new("RGB", (10, 10), color="white").save(image_path)

    with patch(
        "src.app.ocr.extractor.pytesseract.image_to_string", return_value="hello"
    ) as mocked:
        result = extract_text(image_path)

    mocked.assert_called_once()
    assert result == "hello"


def test_extract_text_from_image_skips_preprocessing_when_disabled(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    Image.new("RGB", (10, 10), color="white").save(image_path)

    with patch(
        "src.app.ocr.extractor.pytesseract.image_to_string", return_value=""
    ) as mocked, patch("src.app.ocr.extractor.cv2.cvtColor") as mocked_cvt:
        extract_text_from_image(image_path, preprocess=False)

    mocked_cvt.assert_not_called()
    mocked.assert_called_once()
