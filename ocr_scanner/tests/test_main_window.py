"""Tests for ocr_scanner/ui/main_window.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from PIL import Image
from PyQt6.QtWidgets import QApplication, QMessageBox

from ocr_scanner.core.capture import ScreenCaptureError
from ocr_scanner.core.ocr import OCRError, TextBlock
from ocr_scanner.ui.main_window import AppState, MainWindow, OCRWorker, pil_to_pixmap

# --- AppState tests ---


class TestAppState:
    """Test the AppState enum."""

    def test_all_states_exist(self) -> None:
        assert AppState.IDLE
        assert AppState.CAPTURING
        assert AppState.SELECTING
        assert AppState.SELECTED
        assert AppState.PROCESSING
        assert AppState.RESULT

    def test_states_are_unique(self) -> None:
        states = list(AppState)
        assert len(states) == len(set(states))


# --- OCRWorker tests (no UI) ---


class TestOCRWorker:
    """Test OCRWorker independently without UI."""

    @patch("ocr_scanner.ui.main_window.extract_text")
    @patch("ocr_scanner.ui.main_window.draw_ocr_boxes")
    def test_worker_emits_finished_and_image_ready(
        self, mock_draw: MagicMock, mock_extract: MagicMock, qtbot
    ) -> None:
        mock_blocks = [TextBlock("Hello", 10, 10, 100, 30, 95.0)]
        mock_extract.return_value = mock_blocks
        mock_image = Image.new("RGB", (200, 100), "white")
        mock_draw.return_value = mock_image

        worker = OCRWorker(Image.new("RGB", (100, 100)))
        finished_received: list | None = None
        image_received: Image.Image | None = None

        def on_finished(blocks: list) -> None:
            nonlocal finished_received
            finished_received = blocks

        def on_image_ready(image: Image.Image) -> None:
            nonlocal image_received
            image_received = image

        worker.finished.connect(on_finished)
        worker.image_ready.connect(on_image_ready)

        with qtbot.waitSignal(worker.image_ready, timeout=5000):
            worker.start()

        assert finished_received == mock_blocks
        assert image_received == mock_image

    @patch("ocr_scanner.ui.main_window.extract_text")
    def test_worker_emits_error_on_ocr_failure(
        self, mock_extract: MagicMock, qtbot
    ) -> None:
        mock_extract.side_effect = OCRError("Tesseract not found")
        error_received: str | None = None

        def on_error(msg: str) -> None:
            nonlocal error_received
            error_received = msg

        worker = OCRWorker(Image.new("RGB", (100, 100)))
        worker.error.connect(on_error)

        with qtbot.waitSignal(worker.error, timeout=5000):
            worker.start()

        assert "Tesseract not found" in error_received

    def test_worker_stores_image_and_lang(self) -> None:
        img = Image.new("RGB", (50, 50), "red")
        worker = OCRWorker(img, lang="chi_sim")
        assert worker._image == img
        assert worker._lang == "chi_sim"


# --- MainWindow tests ---


class TestMainWindowCreation:
    """Test MainWindow initialization."""

    def test_window_creates(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        assert window is not None

    def test_initial_state_is_idle(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        assert window._state == AppState.IDLE

    def test_initial_button_states(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        assert window.capture_btn.isEnabled() is True
        assert window.ocr_btn.isEnabled() is False
        assert window.save_btn.isEnabled() is False

    def test_initial_screenshot_is_none(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        assert window._screenshot is None
        assert window._selection is None
        assert window._annotated_image is None


class TestSetState:
    """Test _set_state transitions and button states."""

    def test_set_state_idle(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window._set_state(AppState.IDLE)
        assert window.capture_btn.isEnabled() is True
        assert window.ocr_btn.isEnabled() is False
        assert window.save_btn.isEnabled() is False
        assert "Ready" in window.statusBar().currentMessage()

    def test_set_state_capturing(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window._set_state(AppState.CAPTURING)
        assert window.capture_btn.isEnabled() is False
        assert window.ocr_btn.isEnabled() is False
        assert window.save_btn.isEnabled() is False
        assert "Capturing" in window.statusBar().currentMessage()

    def test_set_state_selecting(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window._set_state(AppState.SELECTING)
        assert window.capture_btn.isEnabled() is True
        assert window.ocr_btn.isEnabled() is False
        assert window.save_btn.isEnabled() is False
        assert "Select" in window.statusBar().currentMessage()

    def test_set_state_selected(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window._set_state(AppState.SELECTED)
        assert window.capture_btn.isEnabled() is True
        assert window.ocr_btn.isEnabled() is True
        assert window.save_btn.isEnabled() is False
        assert "selected" in window.statusBar().currentMessage()

    def test_set_state_processing(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window._set_state(AppState.PROCESSING)
        assert window.capture_btn.isEnabled() is False
        assert window.ocr_btn.isEnabled() is False
        assert window.save_btn.isEnabled() is False
        assert "Processing" in window.statusBar().currentMessage()

    def test_set_state_result(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window._set_state(AppState.RESULT)
        assert window.capture_btn.isEnabled() is True
        assert window.ocr_btn.isEnabled() is False
        assert window.save_btn.isEnabled() is True
        assert "complete" in window.statusBar().currentMessage()


class TestStateTransitions:
    """Test full state transition workflow."""

    @patch("ocr_scanner.ui.main_window.capture_screen")
    def test_idle_to_selecting_via_capture(self, mock_capture: MagicMock, qtbot) -> None:
        mock_capture.return_value = Image.new("RGB", (1920, 1080), "white")
        window = MainWindow()
        qtbot.addWidget(window)

        assert window._state == AppState.IDLE
        window._on_capture()

        assert window._state == AppState.SELECTING
        assert window._screenshot is not None
        mock_capture.assert_called_once()

    def test_selecting_to_selected_via_region(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window._set_state(AppState.SELECTING)

        window._on_region_selected(10, 20, 100, 50)

        assert window._state == AppState.SELECTED
        assert window._selection == (10, 20, 100, 50)

    @patch("ocr_scanner.ui.main_window.extract_text")
    @patch("ocr_scanner.ui.main_window.draw_ocr_boxes")
    def test_selected_to_result_via_ocr(
        self, mock_draw: MagicMock, mock_extract: MagicMock, qtbot
    ) -> None:
        mock_blocks = [TextBlock("Hello", 0, 0, 100, 30, 95.0)]
        mock_extract.return_value = mock_blocks
        mock_annotated = Image.new("RGB", (100, 50), "green")
        mock_draw.return_value = mock_annotated

        window = MainWindow()
        qtbot.addWidget(window)
        window._screenshot = Image.new("RGB", (1920, 1080), "white")
        window._selection = (0, 0, 100, 50)
        window._set_state(AppState.SELECTED)

        # Patch worker.start() to run synchronously for testing
        original_start = OCRWorker.start

        def sync_start(self: OCRWorker) -> None:
            self.run()

        OCRWorker.start = sync_start  # type: ignore[assignment]
        try:
            window._on_ocr()
        finally:
            OCRWorker.start = original_start  # type: ignore[assignment]

        assert window._state == AppState.RESULT
        assert "Hello" in window.text_edit.toPlainText()

    def test_result_to_idle_via_reset(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window._screenshot = Image.new("RGB", (100, 100), "white")
        window._selection = (0, 0, 50, 50)
        window._annotated_image = Image.new("RGB", (100, 100), "green")
        window.text_edit.setPlainText("test text")
        window._set_state(AppState.RESULT)

        window._on_reset()

        assert window._state == AppState.IDLE
        assert window._screenshot is None
        assert window._selection is None
        assert window._annotated_image is None
        assert window.text_edit.toPlainText() == ""


class TestOnCapture:
    """Test _on_capture with mocked capture_screen."""

    @patch("ocr_scanner.ui.main_window.capture_screen")
    def test_capture_success(self, mock_capture: MagicMock, qtbot) -> None:
        mock_capture.return_value = Image.new("RGB", (1920, 1080), "white")
        window = MainWindow()
        qtbot.addWidget(window)

        window._on_capture()

        assert window._state == AppState.SELECTING
        assert window._screenshot is not None
        mock_capture.assert_called_once()

    @patch("ocr_scanner.ui.main_window.capture_screen")
    @patch.object(QMessageBox, "critical", return_value=QMessageBox.StandardButton.Ok)
    def test_capture_failure_shows_error(
        self, mock_msgbox: MagicMock, mock_capture: MagicMock, qtbot
    ) -> None:
        mock_capture.side_effect = ScreenCaptureError("No display")
        window = MainWindow()
        qtbot.addWidget(window)

        window._on_capture()

        assert window._state == AppState.IDLE
        mock_msgbox.assert_called_once()

    @patch("ocr_scanner.ui.main_window.capture_screen")
    def test_capture_sets_pixmap_on_canvas(self, mock_capture: MagicMock, qtbot) -> None:
        mock_capture.return_value = Image.new("RGB", (800, 600), "blue")
        window = MainWindow()
        qtbot.addWidget(window)

        window._on_capture()

        assert window.canvas._pixmap is not None


class TestOnOCR:
    """Test _on_ocr with mocked extract_text."""

    @patch("ocr_scanner.ui.main_window.extract_text")
    @patch("ocr_scanner.ui.main_window.draw_ocr_boxes")
    def test_ocr_starts_worker(
        self, mock_draw: MagicMock, mock_extract: MagicMock, qtbot
    ) -> None:
        mock_blocks = [TextBlock("Test", 0, 0, 50, 20, 90.0)]
        mock_extract.return_value = mock_blocks
        mock_draw.return_value = Image.new("RGB", (50, 20), "white")

        window = MainWindow()
        qtbot.addWidget(window)
        window._screenshot = Image.new("RGB", (200, 200), "white")
        window._selection = (0, 0, 50, 50)

        original_start = OCRWorker.start
        OCRWorker.start = lambda self: self.run()  # type: ignore[assignment]
        try:
            window._on_ocr()
        finally:
            OCRWorker.start = original_start  # type: ignore[assignment]

        mock_extract.assert_called_once()
        assert window._state == AppState.RESULT

    @patch("ocr_scanner.ui.main_window.extract_text")
    @patch("ocr_scanner.ui.main_window.draw_ocr_boxes")
    def test_ocr_sets_processing_state(
        self, mock_draw: MagicMock, mock_extract: MagicMock, qtbot
    ) -> None:
        mock_blocks = [TextBlock("Test", 0, 0, 50, 20, 90.0)]
        mock_extract.return_value = mock_blocks
        mock_draw.return_value = Image.new("RGB", (50, 20), "white")

        window = MainWindow()
        qtbot.addWidget(window)
        window._screenshot = Image.new("RGB", (200, 200), "white")
        window._selection = (0, 0, 50, 50)

        # Check state is PROCESSING immediately after _on_ocr starts
        original_start = OCRWorker.start
        OCRWorker.start = lambda self: self.run()  # type: ignore[assignment]
        try:
            window._on_ocr()
        finally:
            OCRWorker.start = original_start  # type: ignore[assignment]

        assert window._state == AppState.RESULT

    def test_ocr_does_nothing_without_selection(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window._screenshot = None
        window._selection = None

        window._on_ocr()

        assert window._state == AppState.IDLE

    def test_ocr_does_nothing_without_screenshot(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window._screenshot = None
        window._selection = (0, 0, 50, 50)

        window._on_ocr()

        assert window._state == AppState.IDLE


class TestOCRErrorHandling:
    """Test OCR error paths."""

    @patch("ocr_scanner.ui.main_window.extract_text")
    @patch.object(QMessageBox, "warning", return_value=QMessageBox.StandardButton.Ok)
    def test_ocr_error_returns_to_selected(
        self, mock_msgbox: MagicMock, mock_extract: MagicMock, qtbot
    ) -> None:
        mock_extract.side_effect = OCRError("Tesseract not found")

        window = MainWindow()
        qtbot.addWidget(window)
        window._screenshot = Image.new("RGB", (200, 200), "white")
        window._selection = (0, 0, 50, 50)
        window._set_state(AppState.SELECTED)

        original_start = OCRWorker.start
        OCRWorker.start = lambda self: self.run()  # type: ignore[assignment]
        try:
            window._on_ocr()
        finally:
            OCRWorker.start = original_start  # type: ignore[assignment]

        assert window._state == AppState.SELECTED
        mock_msgbox.assert_called_once()


class TestOnSave:
    """Test _on_save functionality."""

    @patch("ocr_scanner.ui.main_window.QFileDialog.getSaveFileName")
    def test_save_with_annotated_image(self, mock_dialog: MagicMock, qtbot) -> None:
        mock_dialog.return_value = ("/tmp/test_save.png", "PNG Images (*.png)")
        window = MainWindow()
        qtbot.addWidget(window)
        window._annotated_image = Image.new("RGB", (100, 100), "green")
        window._set_state(AppState.RESULT)

        window._on_save()

        mock_dialog.assert_called_once()

    @patch("ocr_scanner.ui.main_window.QFileDialog.getSaveFileName")
    def test_save_with_screenshot_fallback(
        self, mock_dialog: MagicMock, qtbot
    ) -> None:
        mock_dialog.return_value = ("/tmp/test_save.png", "PNG Images (*.png)")
        window = MainWindow()
        qtbot.addWidget(window)
        window._screenshot = Image.new("RGB", (100, 100), "blue")
        window._annotated_image = None
        window._set_state(AppState.RESULT)

        window._on_save()

        mock_dialog.assert_called_once()

    def test_save_does_nothing_without_image(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window._screenshot = None
        window._annotated_image = None

        # Should not raise, just return early
        window._on_save()


class TestOnReset:
    """Test _on_reset functionality."""

    def test_reset_clears_everything(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window._screenshot = Image.new("RGB", (100, 100), "white")
        window._selection = (0, 0, 50, 50)
        window._annotated_image = Image.new("RGB", (100, 100), "green")
        window.text_edit.setPlainText("some text")

        window._on_reset()

        assert window._state == AppState.IDLE
        assert window._screenshot is None
        assert window._selection is None
        assert window._annotated_image is None
        assert window.text_edit.toPlainText() == ""


class TestOnCopy:
    """Test copy to clipboard functionality."""

    def test_copy_text_to_clipboard(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window.text_edit.setPlainText("Copied text")

        window._on_copy()

        clipboard = QApplication.clipboard()
        assert clipboard.text() == "Copied text"

    def test_copy_does_nothing_when_empty(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window.text_edit.setPlainText("")

        # Should not raise
        window._on_copy()


class TestOnRegionSelected:
    """Test _on_region_selected handler."""

    def test_stores_selection(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)

        window._on_region_selected(100, 200, 300, 150)

        assert window._selection == (100, 200, 300, 150)
        assert window._state == AppState.SELECTED

    def test_overwrites_previous_selection(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window._selection = (0, 0, 50, 50)

        window._on_region_selected(10, 20, 60, 40)

        assert window._selection == (10, 20, 60, 40)


class TestOCRWorkerSignalConnections:
    """Test that worker signals are properly connected."""

    def test_worker_signals_connected(self, qtbot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        # Verify the worker has the expected signals
        assert hasattr(window.worker, "finished")
        assert hasattr(window.worker, "error")
        assert hasattr(window.worker, "image_ready")


# --- pil_to_pixmap tests ---


class TestPilToPixmap:
    """Test PIL Image to QPixmap conversion."""

    def test_converts_rgb_image(self, qtbot) -> None:
        img = Image.new("RGB", (100, 50), "red")
        pixmap = pil_to_pixmap(img)
        assert pixmap is not None
        assert pixmap.width() == 100
        assert pixmap.height() == 50

    def test_converts_rgba_image(self, qtbot) -> None:
        img = Image.new("RGBA", (200, 100), (255, 0, 0, 128))
        pixmap = pil_to_pixmap(img)
        assert pixmap is not None
        assert pixmap.width() == 200
        assert pixmap.height() == 100
