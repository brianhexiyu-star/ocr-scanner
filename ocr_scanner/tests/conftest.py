"""Shared fixtures and mocks for OCR Scanner tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from ocr_scanner.core.ocr import TextBlock

# --- OCR fixtures ---


@pytest.fixture
def sample_text_blocks() -> list[TextBlock]:
    """Return a list of TextBlock instances with varying confidence levels."""
    return [
        TextBlock(text="Hello World", x=10, y=10, w=100, h=30, confidence=95.0),
        TextBlock(text="Medium text", x=120, y=10, w=80, h=25, confidence=65.0),
        TextBlock(text="Low quality", x=10, y=50, w=90, h=20, confidence=30.0),
    ]


@pytest.fixture
def synthetic_ocr_dict() -> dict:
    """Return a synthetic pytesseract image_to_data() output dict."""
    return {
        "text": ["Hello", "World", "", "Noise", "Valid"],
        "conf": [95, 88, 0, 15, 72],
        "left": [10, 120, 0, 200, 50],
        "top": [10, 10, 0, 50, 60],
        "width": [50, 60, 0, 40, 80],
        "height": [20, 20, 0, 15, 25],
    }


# --- Capture fixtures ---


@pytest.fixture
def mock_mss_data() -> MagicMock:
    """Return mock mss monitor data with synthetic BGRA bytes."""
    width, height = 1920, 1080
    # Create synthetic BGRA bytes (blue screen)
    bgra = b"\x00\x00\xFF\xFF" * (width * height)
    mock = MagicMock()
    mock.size = (width, height)
    mock.bgra = bgra
    return mock


@pytest.fixture
def mock_mss(mock_mss_data: MagicMock) -> MagicMock:
    """Mock mss.mss() context manager with synthetic monitor data."""
    mock_sct = MagicMock()
    mock_sct.monitors = [
        {"left": 0, "top": 0, "width": 3840, "height": 2160},  # combined
        {"left": 0, "top": 0, "width": 1920, "height": 1080},  # monitor 1
        {"left": 1920, "top": 0, "width": 1920, "height": 1080},  # monitor 2
    ]
    mock_sct.grab.return_value = mock_mss_data
    mock_context = MagicMock()
    mock_context.__enter__ = MagicMock(return_value=mock_sct)
    mock_context.__exit__ = MagicMock(return_value=False)
    with patch("ocr_scanner.core.capture.mss.mss", return_value=mock_context):
        yield mock_sct


# --- Image fixtures ---


@pytest.fixture
def sample_pil_image() -> Image.Image:
    """Return a small synthetic PIL Image for testing."""
    return Image.new("RGB", (200, 100), color="white")


@pytest.fixture
def sample_pixmap(qtbot) -> QPixmap:  # type: ignore[misc]
    """Return a synthetic QPixmap for canvas testing."""
    pixmap = QPixmap(1920, 1080)
    pixmap.fill(Qt.GlobalColor.white)
    return pixmap
