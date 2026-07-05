"""Arabic/English OCR extraction for images and PDFs using Tesseract."""

import os
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from dotenv import load_dotenv
from loguru import logger
from PIL import Image

load_dotenv()

DEFAULT_LANG = "ara+eng"

_DEFAULT_TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_TESSDATA_DIR = _PROJECT_ROOT / "models_store" / "tessdata"

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
_PDF_EXTENSIONS = {".pdf"}


def _configure_tesseract() -> None:
    tesseract_cmd = os.getenv("TESSERACT_CMD") or _DEFAULT_TESSERACT_CMD
    if Path(tesseract_cmd).exists():
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    tessdata_dir = os.getenv("TESSDATA_PREFIX")
    if not tessdata_dir and _DEFAULT_TESSDATA_DIR.exists():
        tessdata_dir = str(_DEFAULT_TESSDATA_DIR)
    if tessdata_dir:
        os.environ["TESSDATA_PREFIX"] = tessdata_dir


_configure_tesseract()


def _get_poppler_path() -> str | None:
    return os.getenv("POPPLER_PATH") or None


def preprocess_image(image: Image.Image) -> Image.Image:
    """Grayscale + adaptive threshold to improve OCR accuracy on scanned documents."""
    gray = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2GRAY)
    thresholded = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )
    return Image.fromarray(thresholded)


def extract_text_from_image(
    image: str | Path | Image.Image, lang: str = DEFAULT_LANG, preprocess: bool = True
) -> str:
    """Extract text from a single image file or PIL.Image."""
    if isinstance(image, (str, Path)):
        image_path = Path(image)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        pil_image = Image.open(image_path)
    else:
        pil_image = image

    if preprocess:
        pil_image = preprocess_image(pil_image)

    logger.info("Running Tesseract OCR (lang={}) on image", lang)
    return pytesseract.image_to_string(pil_image, lang=lang)


def extract_text_from_pdf(pdf_path: str | Path, lang: str = DEFAULT_LANG, dpi: int = 300) -> str:
    """Extract text from every page of a PDF and join the results."""
    from pdf2image import convert_from_path

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    logger.info("Converting PDF to images (dpi={}): {}", dpi, pdf_path)
    pages = convert_from_path(str(pdf_path), dpi=dpi, poppler_path=_get_poppler_path())

    page_texts = [
        extract_text_from_image(page, lang=lang) for page in pages
    ]
    return "\n\n".join(page_texts)


def extract_text(file_path: str | Path, lang: str = DEFAULT_LANG) -> str:
    """Extract Arabic/English text from an image or PDF file, detected by extension."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix in _PDF_EXTENSIONS:
        return extract_text_from_pdf(file_path, lang=lang)
    if suffix in _IMAGE_EXTENSIONS:
        return extract_text_from_image(file_path, lang=lang)

    raise ValueError(f"Unsupported file type '{suffix}': {file_path}")
