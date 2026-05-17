"""Unit tests for ocr_scanner.core.ocr module."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from PIL import Image

from ocr_scanner.core.ocr import (
    CONFIDENCE_COLORS,
    OCRError,
    TextBlock,
    draw_ocr_boxes,
    extract_text,
    validate_tesseract,
)

# --- TextBlock confidence property tests ---


class TestTextBlockConfidence:
    """Test TextBlock confidence classification boundaries."""

    def test_high_confidence_above_80(self) -> None:
        block = TextBlock(text="test", x=0, y=0, w=10, h=10, confidence=81.0)
        assert block.is_high_confidence is True
        assert block.is_medium_confidence is False
        assert block.is_low_confidence is False

    def test_high_confidence_100(self) -> None:
        block = TextBlock(text="test", x=0, y=0, w=10, h=10, confidence=100.0)
        assert block.is_high_confidence is True
        assert block.is_medium_confidence is False
        assert block.is_low_confidence is False

    def test_medium_confidence_boundary_80(self) -> None:
        """At exactly 80.0, should be medium (not high)."""
        block = TextBlock(text="test", x=0, y=0, w=10, h=10, confidence=80.0)
        assert block.is_high_confidence is False
        assert block.is_medium_confidence is True
        assert block.is_low_confidence is False

    def test_medium_confidence_middle_range(self) -> None:
        block = TextBlock(text="test", x=0, y=0, w=10, h=10, confidence=65.0)
        assert block.is_high_confidence is False
        assert block.is_medium_confidence is True
        assert block.is_low_confidence is False

    def test_low_confidence_boundary_50(self) -> None:
        """At exactly 50.0, should be low."""
        block = TextBlock(text="test", x=0, y=0, w=10, h=10, confidence=50.0)
        assert block.is_high_confidence is False
        assert block.is_medium_confidence is False
        assert block.is_low_confidence is True

    def test_low_confidence_zero(self) -> None:
        block = TextBlock(text="test", x=0, y=0, w=10, h=10, confidence=0.0)
        assert block.is_high_confidence is False
        assert block.is_medium_confidence is False
        assert block.is_low_confidence is True

    def test_low_confidence_just_above_50(self) -> None:
        block = TextBlock(text="test", x=0, y=0, w=10, h=10, confidence=50.1)
        assert block.is_high_confidence is False
        assert block.is_medium_confidence is True
        assert block.is_low_confidence is False

    def test_medium_confidence_just_below_80(self) -> None:
        block = TextBlock(text="test", x=0, y=0, w=10, h=10, confidence=79.9)
        assert block.is_high_confidence is False
        assert block.is_medium_confidence is True
        assert block.is_low_confidence is False


# --- extract_text() tests ---


class TestExtractText:
    """Test extract_text() with mocked pytesseract."""

    def test_extract_text_returns_blocks_from_synthetic_dict(
        self, synthetic_ocr_dict: dict
    ) -> None:
        """Test that extract_text parses synthetic OCR dict correctly."""
        with patch(
            "ocr_scanner.core.ocr.pytesseract.image_to_data",
            return_value=synthetic_ocr_dict,
        ):
            image = Image.new("RGB", (200, 100), "white")
            blocks = extract_text(image)

        # synthetic_ocr_dict has 5 entries:
        # "Hello" (conf=95), "World" (conf=88), "" (conf=0), "Noise" (conf=15), "Valid" (conf=72)
        # Filtered: "" (conf=0) is excluded, but "Noise" (conf=15) and "Valid" (conf=72) pass
        assert len(blocks) == 4
        assert blocks[0].text == "Hello"
        assert blocks[0].confidence == 95.0
        assert blocks[0].x == 10
        assert blocks[0].y == 10
        assert blocks[0].w == 50
        assert blocks[0].h == 20

    def test_extract_text_filters_empty_strings(self) -> None:
        """Test that entries with empty text are filtered out."""
        mock_data = {
            "text": ["", "Valid", "  ", "Another"],
            "conf": [90, 85, 70, 60],
            "left": [0, 10, 20, 30],
            "top": [0, 10, 20, 30],
            "width": [10, 20, 30, 40],
            "height": [10, 20, 30, 40],
        }
        with patch(
            "ocr_scanner.core.ocr.pytesseract.image_to_data", return_value=mock_data
        ):
            image = Image.new("RGB", (100, 100), "white")
            blocks = extract_text(image)

        # "" and "  " (whitespace-only after strip) should be filtered
        assert len(blocks) == 2
        assert blocks[0].text == "Valid"
        assert blocks[1].text == "Another"

    def test_extract_text_filters_conf_zero(self) -> None:
        """Test that entries with conf <= 0 are filtered out."""
        mock_data = {
            "text": ["Valid", "Zero", "Negative"],
            "conf": [80, 0, -1],
            "left": [0, 10, 20],
            "top": [0, 10, 20],
            "width": [10, 20, 30],
            "height": [10, 20, 30],
        }
        with patch(
            "ocr_scanner.core.ocr.pytesseract.image_to_data", return_value=mock_data
        ):
            image = Image.new("RGB", (100, 100), "white")
            blocks = extract_text(image)

        assert len(blocks) == 1
        assert blocks[0].text == "Valid"

    def test_extract_text_raises_ocr_error_on_failure(self) -> None:
        """Test that OCRError is raised when pytesseract fails."""
        with patch(
            "ocr_scanner.core.ocr.pytesseract.image_to_data",
            side_effect=RuntimeError("Tesseract not found"),
        ):
            image = Image.new("RGB", (100, 100), "white")
            with pytest.raises(OCRError, match="OCR processing failed"):
                extract_text(image)

    def test_extract_text_returns_empty_list_when_no_text(self) -> None:
        """Test that empty result is returned when no text detected."""
        mock_data = {
            "text": ["", "", ""],
            "conf": [0, 0, 0],
            "left": [0, 0, 0],
            "top": [0, 0, 0],
            "width": [0, 0, 0],
            "height": [0, 0, 0],
        }
        with patch(
            "ocr_scanner.core.ocr.pytesseract.image_to_data", return_value=mock_data
        ):
            image = Image.new("RGB", (100, 100), "white")
            blocks = extract_text(image)

        assert blocks == []

    def test_extract_text_with_custom_lang(self) -> None:
        """Test that lang parameter is passed through."""
        mock_data = {
            "text": ["Test"],
            "conf": [90],
            "left": [10],
            "top": [10],
            "width": [50],
            "height": [20],
        }
        with patch(
            "ocr_scanner.core.ocr.pytesseract.image_to_data", return_value=mock_data
        ) as mock_func:
            image = Image.new("RGB", (100, 100), "white")
            extract_text(image, lang="chi_sim")

        mock_func.assert_called_once_with(
            image, lang="chi_sim", output_type=pytest.importorskip("pytesseract").Output.DICT
        )


# --- draw_ocr_boxes() tests ---


class TestDrawOCRBoxes:
    """Test draw_ocr_boxes() draws correct colors at expected coordinates."""

    def test_draw_ocr_boxes_returns_new_image(
        self, sample_pil_image: Image.Image, sample_text_blocks: list[TextBlock]
    ) -> None:
        """Test that draw_ocr_boxes returns a new image, not modifying original."""
        original = sample_pil_image.copy()
        result = draw_ocr_boxes(sample_pil_image, sample_text_blocks)

        assert result is not sample_pil_image
        # Original should be unchanged
        assert list(sample_pil_image.getdata()) == list(original.getdata())

    def test_draw_ocr_boxes_high_confidence_green(
        self, sample_pil_image: Image.Image
    ) -> None:
        """Test that high confidence blocks draw green boxes."""
        block = TextBlock(text="test", x=10, y=10, w=20, h=20, confidence=95.0)
        result = draw_ocr_boxes(sample_pil_image, [block])

        # Check a pixel on the top edge of the rectangle
        # The rectangle goes from (10,10) to (30,30)
        # With line_width=2, pixels at (10,10), (11,10), (10,11), (10,12) should be green
        pixel = result.getpixel((10, 10))
        assert pixel == CONFIDENCE_COLORS["high"], f"Expected green, got {pixel}"

    def test_draw_ocr_boxes_medium_confidence_yellow(
        self, sample_pil_image: Image.Image
    ) -> None:
        """Test that medium confidence blocks draw yellow boxes."""
        block = TextBlock(text="test", x=50, y=50, w=20, h=20, confidence=65.0)
        result = draw_ocr_boxes(sample_pil_image, [block])

        pixel = result.getpixel((50, 50))
        assert pixel == CONFIDENCE_COLORS["medium"], f"Expected yellow, got {pixel}"

    def test_draw_ocr_boxes_low_confidence_red(
        self, sample_pil_image: Image.Image
    ) -> None:
        """Test that low confidence blocks draw red boxes."""
        block = TextBlock(text="test", x=100, y=10, w=20, h=20, confidence=30.0)
        result = draw_ocr_boxes(sample_pil_image, [block])

        pixel = result.getpixel((100, 10))
        assert pixel == CONFIDENCE_COLORS["low"], f"Expected red, got {pixel}"

    def test_draw_ocr_boxes_multiple_colors(
        self, sample_pil_image: Image.Image, sample_text_blocks: list[TextBlock]
    ) -> None:
        """Test that multiple blocks with different confidences draw correct colors."""
        result = draw_ocr_boxes(sample_pil_image, sample_text_blocks)

        # First block: confidence=95.0 (high) at (10, 10)
        assert result.getpixel((10, 10)) == CONFIDENCE_COLORS["high"]

        # Second block: confidence=65.0 (medium) at (120, 10)
        assert result.getpixel((120, 10)) == CONFIDENCE_COLORS["medium"]

        # Third block: confidence=30.0 (low) at (10, 50)
        assert result.getpixel((10, 50)) == CONFIDENCE_COLORS["low"]

    def test_draw_ocr_boxes_custom_line_width(
        self, sample_pil_image: Image.Image
    ) -> None:
        """Test that custom line_width is applied."""
        block = TextBlock(text="test", x=10, y=10, w=20, h=20, confidence=95.0)
        result = draw_ocr_boxes(sample_pil_image, [block], line_width=5)

        # With line_width=5, pixel at (12, 12) should still be on the border
        pixel = result.getpixel((12, 12))
        assert pixel == CONFIDENCE_COLORS["high"]

    def test_draw_ocr_boxes_empty_blocks_list(
        self, sample_pil_image: Image.Image
    ) -> None:
        """Test that empty blocks list returns unchanged image copy."""
        result = draw_ocr_boxes(sample_pil_image, [])
        assert result.size == sample_pil_image.size
        assert result.mode == "RGB"

    def test_draw_ocr_boxes_converts_to_rgb(self) -> None:
        """Test that non-RGB images are converted to RGB."""
        image = Image.new("L", (100, 100), 128)  # Grayscale
        block = TextBlock(text="test", x=10, y=10, w=20, h=20, confidence=95.0)
        result = draw_ocr_boxes(image, [block])

        assert result.mode == "RGB"


# --- validate_tesseract() tests ---


class TestValidateTesseract:
    """Test validate_tesseract() returns bool without crashing."""

    def test_validate_tesseract_returns_true_when_available(self) -> None:
        """Test that validate_tesseract returns True when tesseract is available."""
        with patch(
            "ocr_scanner.core.ocr.pytesseract.get_tesseract_version",
            return_value="5.3.0",
        ):
            result = validate_tesseract()

        assert result is True

    def test_validate_tesseract_returns_false_when_not_available(self) -> None:
        """Test that validate_tesseract returns False when tesseract is not available."""
        with patch(
            "ocr_scanner.core.ocr.pytesseract.get_tesseract_version",
            side_effect=FileNotFoundError("Tesseract not found"),
        ):
            result = validate_tesseract()

        assert result is False

    def test_validate_tesseract_returns_false_on_any_exception(self) -> None:
        """Test that validate_tesseract returns False on any exception."""
        with patch(
            "ocr_scanner.core.ocr.pytesseract.get_tesseract_version",
            side_effect=RuntimeError("Some error"),
        ):
            result = validate_tesseract()

        assert result is False

    def test_validate_tesseract_does_not_crash(self) -> None:
        """Test that validate_tesseract never raises an exception."""
        # Without any mocking, this should still not crash
        result = validate_tesseract()
        assert isinstance(result, bool)
