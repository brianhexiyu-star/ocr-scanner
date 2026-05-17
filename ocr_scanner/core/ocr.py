"""OCR processing module — pure logic, no UI dependency."""

from __future__ import annotations

from dataclasses import dataclass

import pytesseract
from PIL import Image, ImageDraw


class OCRError(Exception):
    """Raised when OCR processing fails."""

    pass


@dataclass
class TextBlock:
    """Represents a single OCR-detected text element."""

    text: str
    x: int  # Left coordinate (image pixels)
    y: int  # Top coordinate (image pixels)
    w: int  # Width in pixels
    h: int  # Height in pixels
    confidence: float  # 0.0 - 100.0

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence > 80.0

    @property
    def is_medium_confidence(self) -> bool:
        return 50.0 < self.confidence <= 80.0

    @property
    def is_low_confidence(self) -> bool:
        return self.confidence <= 50.0


CONFIDENCE_COLORS: dict[str, tuple[int, int, int]] = {
    "high": (0, 255, 0),  # Green
    "medium": (255, 255, 0),  # Yellow
    "low": (255, 0, 0),  # Red
}


def extract_text(image: Image.Image, lang: str = "eng") -> list[TextBlock]:
    """Run OCR on the given image and return structured text blocks.

    Args:
        image: PIL.Image.Image (any mode, will be converted to grayscale internally).
        lang: Tesseract language code (default: "eng").

    Returns:
        List of TextBlock, sorted by reading order (top-to-bottom, left-to-right).
        Empty list if no text detected.

    Raises:
        OCRError: If Tesseract binary is not found or processing fails.
    """
    try:
        data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
        blocks: list[TextBlock] = []
        for i in range(len(data["text"])):
            conf = int(data["conf"][i])
            text = data["text"][i].strip()
            if conf > 0 and text:
                blocks.append(
                    TextBlock(
                        text=text,
                        x=data["left"][i],
                        y=data["top"][i],
                        w=data["width"][i],
                        h=data["height"][i],
                        confidence=float(conf),
                    )
                )
        return blocks
    except Exception as e:
        raise OCRError(f"OCR processing failed: {e}") from e


def draw_ocr_boxes(
    image: Image.Image,
    blocks: list[TextBlock],
    line_width: int = 2,
) -> Image.Image:
    """Draw colored bounding boxes on a copy of the image.

    Color scheme:
        - Green: confidence > 80%
        - Yellow: 50% < confidence <= 80%
        - Red: confidence <= 50%

    Args:
        image: Source PIL.Image.Image.
        blocks: List of TextBlock to annotate.
        line_width: Border width in pixels.

    Returns:
        New PIL.Image.Image with boxes drawn (original unchanged).
    """
    result = image.copy().convert("RGB")
    draw = ImageDraw.Draw(result)
    for block in blocks:
        if block.is_high_confidence:
            color = CONFIDENCE_COLORS["high"]
        elif block.is_medium_confidence:
            color = CONFIDENCE_COLORS["medium"]
        else:
            color = CONFIDENCE_COLORS["low"]
        draw.rectangle(
            [(block.x, block.y), (block.x + block.w, block.y + block.h)],
            outline=color,
            width=line_width,
        )
    return result


def validate_tesseract() -> bool:
    """Check if Tesseract binary is available on PATH.

    Returns:
        True if accessible, False otherwise.
    """
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False
