"""Generates a synthetic Arabic/English engineering-document image for OCR testing."""

from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont

DEFAULT_SAMPLE_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "samples" / "sample_engineering_doc.png"
)

_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
]

_LINES = [
    "تقرير الصيانة الدورية - Maintenance Report",
    "رقم المعدة: PUMP-102",
    "الموقع: محطة الضخ الرئيسية - Main Pumping Station",
    "الحالة: يحتاج صيانة عاجلة - Status: Urgent",
    "تاريخ الفحص: 2026-07-05",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for font_path in _FONT_CANDIDATES:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size)
    raise FileNotFoundError(
        f"No Arabic-capable font found among: {_FONT_CANDIDATES}"
    )


def _render_line(line: str) -> str:
    """Shape and reorder Arabic text so it draws correctly with PIL (no raqm)."""
    reshaped = arabic_reshaper.reshape(line)
    return get_display(reshaped)


def generate_sample_image(output_path: Path = DEFAULT_SAMPLE_PATH) -> Path:
    """Create a white-background PNG with mixed Arabic/English engineering text."""
    font = _load_font(size=32)
    width, height = 1000, 300
    image = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(image)

    y = 20
    for line in _LINES:
        draw.text((30, y), _render_line(line), font=font, fill="black")
        y += 50

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path


if __name__ == "__main__":
    path = generate_sample_image()
    print(f"Sample image written to: {path}")
