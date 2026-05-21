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

    Uses Tesseract's word-level output (level 5). Each block represents
    one detected word with its bounding box and confidence.

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
            if data["level"][i] != 5:  # 5 = word level
                continue
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


def extract_text_simple(image: Image.Image, lang: str = "eng") -> str:
    """Run OCR on the given image and return the recognized text.

    Uses Tesseract's image_to_string which returns text with lines
    already properly separated.

    Args:
        image: PIL.Image.Image (any mode, will be converted to grayscale internally).
        lang: Tesseract language code (default: "eng").

    Returns:
        Recognized text string, stripped of leading/trailing whitespace.
        Empty string if no text detected.

    Raises:
        OCRError: If Tesseract binary is not found or processing fails.
    """
    try:
        text = pytesseract.image_to_string(image, lang=lang)
        return text.strip()
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


def combine_lines(blocks: list[TextBlock], y_tolerance: int = 10) -> str:
    """Group word-level blocks into lines by y-coordinate and combine text.

    Blocks on the same visual line (within y_tolerance pixels) are joined
    with spaces. Lines are separated by newlines.

    Args:
        blocks: List of word-level TextBlock from OCR.
        y_tolerance: Maximum vertical distance (in pixels) to consider blocks
                     as being on the same line.

    Returns:
        Combined text string with same-line words joined by spaces.
    """
    if not blocks:
        return ""

    sorted_blocks = sorted(blocks, key=lambda b: (b.y, b.x))

    lines: list[list[TextBlock]] = []
    current_line: list[TextBlock] = [sorted_blocks[0]]

    for block in sorted_blocks[1:]:
        avg_y = sum(b.y for b in current_line) / len(current_line)
        if abs(block.y - avg_y) <= y_tolerance:
            current_line.append(block)
        else:
            lines.append(current_line)
            current_line = [block]

    lines.append(current_line)

    return "\n".join(" ".join(b.text for b in line) for line in lines)


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
