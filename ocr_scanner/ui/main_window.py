"""Main window, controls, and orchestration for OCR Scanner."""

from __future__ import annotations

from enum import Enum, auto

from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ocr_scanner.core.capture import ScreenCaptureError, capture_screen
from ocr_scanner.core.ocr import OCRError, TextBlock, draw_ocr_boxes, extract_text
from ocr_scanner.ui.canvas import Canvas


class AppState(Enum):
    """Application state machine states."""

    IDLE = auto()  # Initial state, placeholder displayed
    CAPTURING = auto()  # Screen capture in progress
    SELECTING = auto()  # Screenshot displayed, waiting for region selection
    SELECTED = auto()  # Region selected, OCR button enabled
    PROCESSING = auto()  # OCR running in background thread
    RESULT = auto()  # OCR result displayed, save button enabled


class OCRWorker(QThread):
    """Runs OCR in a background thread to avoid freezing the UI."""

    finished = pyqtSignal(list)  # Emits List[TextBlock]
    error = pyqtSignal(str)  # Emits error message string
    image_ready = pyqtSignal(object)  # Emits annotated PIL.Image

    def __init__(self, image: Image.Image, lang: str = "eng") -> None:
        super().__init__()
        self._image = image
        self._lang = lang

    def run(self) -> None:
        try:
            blocks = extract_text(self._image, lang=self._lang)
            annotated = draw_ocr_boxes(self._image, blocks)
            self.finished.emit(blocks)
            self.image_ready.emit(annotated)
        except OCRError as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window orchestrating capture, OCR, and display."""

    def __init__(self) -> None:
        super().__init__()
        self._state = AppState.IDLE
        self._screenshot: Image.Image | None = None
        self._selection: tuple[int, int, int, int] | None = None
        self._annotated_image: Image.Image | None = None
        self._status_bar: QStatusBar

        self.setWindowTitle("OCR Scanner")
        self.resize(1200, 800)

        # Create UI components
        self.canvas = Canvas()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)

        self.capture_btn = QPushButton("Capture")
        self.ocr_btn = QPushButton("OCR")
        self.save_btn = QPushButton("Save")
        self.reset_btn = QPushButton("Reset")
        self.copy_btn = QPushButton("Copy to Clipboard")

        self.worker: OCRWorker = OCRWorker(Image.new("RGB", (1, 1)))

        self._setup_ui()
        self._connect_signals()
        self._set_state(AppState.IDLE)

    def _setup_ui(self) -> None:
        """Build the UI layout: canvas, buttons, text panel."""
        # Central widget with horizontal layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # Left: Canvas
        main_layout.addWidget(self.canvas, stretch=2)

        # Right: Text panel
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.text_edit, stretch=1)
        right_layout.addWidget(self.copy_btn)
        main_layout.addLayout(right_layout, stretch=1)

        # Toolbar
        toolbar = QToolBar()
        toolbar.addWidget(self.capture_btn)
        toolbar.addWidget(self.ocr_btn)
        toolbar.addWidget(self.save_btn)
        toolbar.addWidget(self.reset_btn)
        self.addToolBar(toolbar)

        # Status bar
        bar = self.statusBar()
        assert bar is not None
        self._status_bar = bar
        self._status_bar.showMessage("Ready")

    def _set_state(self, state: AppState) -> None:
        """Transition to a new state. Updates button enabled states and status bar."""
        self._state = state

        # Button states per state
        if state == AppState.IDLE:
            self.capture_btn.setEnabled(True)
            self.ocr_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self._status_bar.showMessage("Ready")
        elif state == AppState.CAPTURING:
            self.capture_btn.setEnabled(False)
            self.ocr_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self._status_bar.showMessage("Capturing...")
        elif state == AppState.SELECTING:
            self.capture_btn.setEnabled(True)
            self.ocr_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self._status_bar.showMessage("Select a region to OCR")
        elif state == AppState.SELECTED:
            self.capture_btn.setEnabled(True)
            self.ocr_btn.setEnabled(True)
            self.save_btn.setEnabled(False)
            self._status_bar.showMessage("Region selected — click OCR to process")
        elif state == AppState.PROCESSING:
            self.capture_btn.setEnabled(False)
            self.ocr_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self._status_bar.showMessage("Processing OCR...")
        elif state == AppState.RESULT:
            self.capture_btn.setEnabled(True)
            self.ocr_btn.setEnabled(False)
            self.save_btn.setEnabled(True)
            self._status_bar.showMessage("OCR complete — save or reset")

    def _connect_signals(self) -> None:
        """Wire up button clicks, canvas signals, worker signals."""
        # Buttons
        self.capture_btn.clicked.connect(self._on_capture)
        self.ocr_btn.clicked.connect(self._on_ocr)
        self.save_btn.clicked.connect(self._on_save)
        self.reset_btn.clicked.connect(self._on_reset)
        self.copy_btn.clicked.connect(self._on_copy)

        # Canvas
        self.canvas.region_selected.connect(self._on_region_selected)

        # Worker
        self.worker.finished.connect(self._on_ocr_finished)
        self.worker.error.connect(self._on_ocr_error)
        self.worker.image_ready.connect(self._on_ocr_image_ready)

    def _on_capture(self) -> None:
        """Handle capture button click."""
        self._set_state(AppState.CAPTURING)
        try:
            image = capture_screen()
            self._screenshot = image
            pixmap = pil_to_pixmap(image)
            self.canvas.set_image(pixmap)
            self._set_state(AppState.SELECTING)
        except ScreenCaptureError as e:
            QMessageBox.critical(self, "Capture Error", str(e))
            self._set_state(AppState.IDLE)

    def _on_region_selected(self, x: int, y: int, w: int, h: int) -> None:
        """Handle region selection from canvas.

        Crops the screenshot to the selected region and displays it
        so the user can verify what will be OCR'd.
        """
        self._selection = (x, y, w, h)

        # Show the cropped region on the canvas for verification
        if self._screenshot is not None:
            cropped = self._screenshot.crop((x, y, x + w, y + h))
            pixmap = pil_to_pixmap(cropped)
            self.canvas.set_image(pixmap)

        self._set_state(AppState.SELECTED)

    def _on_ocr(self) -> None:
        """Handle OCR button click."""
        if self._selection is None or self._screenshot is None:
            return

        self._set_state(AppState.PROCESSING)

        x, y, w, h = self._selection
        cropped = self._screenshot.crop((x, y, x + w, y + h))

        self.worker = OCRWorker(cropped)
        self.worker.finished.connect(self._on_ocr_finished)
        self.worker.error.connect(self._on_ocr_error)
        self.worker.image_ready.connect(self._on_ocr_image_ready)
        self.worker.start()

    def _on_ocr_finished(self, blocks: list[TextBlock]) -> None:
        """Handle OCR completion."""
        text = "\n".join(block.text for block in blocks)
        self.text_edit.setPlainText(text)
        self._set_state(AppState.RESULT)

    def _on_ocr_image_ready(self, image: Image.Image) -> None:
        """Handle annotated image from OCR worker."""
        self._annotated_image = image
        pixmap = pil_to_pixmap(image)
        self.canvas.set_image(pixmap)

    def _on_ocr_error(self, msg: str) -> None:
        """Handle OCR error."""
        QMessageBox.warning(self, "OCR Error", msg)
        self._set_state(AppState.SELECTED)

    def _on_save(self) -> None:
        """Handle save button click."""
        if self._annotated_image is None and self._screenshot is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Images (*.png)")
        if file_path:
            try:
                image = self._annotated_image or self._screenshot
                if image:
                    image.save(file_path, "PNG")
            except OSError as e:
                QMessageBox.warning(self, "Save Error", str(e))

    def _on_reset(self) -> None:
        """Handle reset button click."""
        self.canvas.clear()
        self.text_edit.clear()
        self._screenshot = None
        self._selection = None
        self._annotated_image = None
        self._set_state(AppState.IDLE)

    def _on_copy(self) -> None:
        """Copy text from text panel to clipboard."""
        text = self.text_edit.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            assert clipboard is not None
            clipboard.setText(text)


def pil_to_pixmap(pil_image: Image.Image) -> QPixmap:
    """Convert a PIL Image to a QPixmap."""
    qimage = ImageQt(pil_image)
    return QPixmap.fromImage(qimage)
