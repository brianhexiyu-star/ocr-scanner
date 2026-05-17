"""Unit tests for ocr_scanner.core.capture module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from ocr_scanner.core.capture import ScreenCaptureError, capture_screen, get_monitor_count


class TestCaptureScreen:
    """Tests for capture_screen() function."""

    def test_capture_screen_returns_pil_image(
        self, mock_mss: MagicMock, mock_mss_data: MagicMock
    ) -> None:
        """capture_screen() returns a valid PIL Image with mocked mss."""
        result = capture_screen(monitor=1)

        assert isinstance(result, Image.Image)

    def test_capture_screen_image_mode_is_rgb(
        self, mock_mss: MagicMock, mock_mss_data: MagicMock
    ) -> None:
        """Captured image mode is RGB."""
        result = capture_screen(monitor=1)

        assert result.mode == "RGB"

    def test_capture_screen_image_size_matches_mock_data(
        self, mock_mss: MagicMock, mock_mss_data: MagicMock
    ) -> None:
        """Captured image size matches mock monitor data."""
        result = capture_screen(monitor=1)

        assert result.size == mock_mss_data.size
        assert result.size == (1920, 1080)

    def test_capture_screen_uses_correct_monitor_index(self, mock_mss: MagicMock) -> None:
        """capture_screen() accesses the correct monitor index."""
        capture_screen(monitor=2)

        mock_mss.grab.assert_called_once()
        call_arg = mock_mss.grab.call_args[0][0]
        assert call_arg == mock_mss.monitors[2]

    def test_capture_screen_default_monitor_is_1(self, mock_mss: MagicMock) -> None:
        """capture_screen() defaults to monitor 1."""
        capture_screen()

        call_arg = mock_mss.grab.call_args[0][0]
        assert call_arg == mock_mss.monitors[1]

    def test_capture_screen_raises_on_grab_failure(self) -> None:
        """ScreenCaptureError is raised when mss.grab() raises."""
        mock_sct = MagicMock()
        mock_sct.monitors = [{"left": 0, "top": 0, "width": 1920, "height": 1080}]
        mock_sct.grab.side_effect = Exception("display not found")
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=mock_sct)
        mock_context.__exit__ = MagicMock(return_value=False)

        with patch("ocr_scanner.core.capture.mss.mss", return_value=mock_context):
            with pytest.raises(ScreenCaptureError, match="Failed to capture screen"):
                capture_screen(monitor=1)

    def test_capture_screen_error_preserves_original_exception(self) -> None:
        """ScreenCaptureError chains the original exception."""
        mock_sct = MagicMock()
        mock_sct.monitors = [
            {"left": 0, "top": 0, "width": 1920, "height": 1080},
            {"left": 0, "top": 0, "width": 1920, "height": 1080},
        ]
        original_error = PermissionError("screen recording permission denied")
        mock_sct.grab.side_effect = original_error
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=mock_sct)
        mock_context.__exit__ = MagicMock(return_value=False)

        with patch("ocr_scanner.core.capture.mss.mss", return_value=mock_context):
            with pytest.raises(ScreenCaptureError) as exc_info:
                capture_screen(monitor=1)

        assert exc_info.value.__cause__ is original_error


class TestGetMonitorCount:
    """Tests for get_monitor_count() function."""

    def test_get_monitor_count_returns_correct_count(self, mock_mss: MagicMock) -> None:
        """get_monitor_count() returns the correct number of monitors."""
        result = get_monitor_count()

        # conftest defines 3 monitors (0=combined, 1, 2), so count = 3 - 1 = 2
        assert result == 2

    def test_get_monitor_count_single_monitor(self) -> None:
        """get_monitor_count() returns 1 for a single monitor setup."""
        mock_sct = MagicMock()
        mock_sct.monitors = [
            {"left": 0, "top": 0, "width": 1920, "height": 1080},  # combined
            {"left": 0, "top": 0, "width": 1920, "height": 1080},  # monitor 1
        ]
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=mock_sct)
        mock_context.__exit__ = MagicMock(return_value=False)

        with patch("ocr_scanner.core.capture.mss.mss", return_value=mock_context):
            result = get_monitor_count()

        assert result == 1

    def test_get_monitor_count_triple_monitor(self) -> None:
        """get_monitor_count() returns 3 for a triple monitor setup."""
        mock_sct = MagicMock()
        mock_sct.monitors = [
            {"left": 0, "top": 0, "width": 5760, "height": 1080},  # combined
            {"left": 0, "top": 0, "width": 1920, "height": 1080},  # monitor 1
            {"left": 1920, "top": 0, "width": 1920, "height": 1080},  # monitor 2
            {"left": 3840, "top": 0, "width": 1920, "height": 1080},  # monitor 3
        ]
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=mock_sct)
        mock_context.__exit__ = MagicMock(return_value=False)

        with patch("ocr_scanner.core.capture.mss.mss", return_value=mock_context):
            result = get_monitor_count()

        assert result == 3


class TestScreenCaptureError:
    """Tests for ScreenCaptureError exception class."""

    def test_is_exception_subclass(self) -> None:
        """ScreenCaptureError is a subclass of Exception."""
        assert issubclass(ScreenCaptureError, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        """ScreenCaptureError can be raised and caught."""
        with pytest.raises(ScreenCaptureError):
            raise ScreenCaptureError("test error")

    def test_error_message_preserved(self) -> None:
        """ScreenCaptureError preserves the error message."""
        with pytest.raises(ScreenCaptureError, match="custom error message"):
            raise ScreenCaptureError("custom error message")
