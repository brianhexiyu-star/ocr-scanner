"""Application entry point for OCR Scanner."""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so `ocr_scanner` package is importable
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from PyQt6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from ocr_scanner.core.ocr import validate_tesseract  # noqa: E402
from ocr_scanner.ui.main_window import MainWindow  # noqa: E402


def main() -> None:
    """Initialize Qt application, perform pre-flight checks, and show main window."""
    app = QApplication(sys.argv)
    app.setApplicationName("OCR Scanner")
    app.setApplicationVersion("0.1.0")

    # Pre-flight check
    if not validate_tesseract():
        QMessageBox.critical(
            None,
            "Missing Dependency",
            "Tesseract OCR engine is not installed.\n\n"
            "macOS: brew install tesseract\n"
            "Ubuntu: sudo apt install tesseract-ocr\n"
            "Windows: Download from github.com/UB-Mannheim/tesseract/wiki",
        )
        sys.exit(1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
