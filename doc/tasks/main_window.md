# Module: `ui/main_window.py` — Task List

> **Design Reference**: `doc/detailed-design.md` §5
> **Dependencies**: `PyQt6`, `core/capture`, `core/ocr`, `ui/canvas`
> **Test Isolation**: Mock `core/*` functions, `pytest-qt` for UI simulation

## Tasks

- [x] **4.1 Create module skeleton**
  - Create `ocr_scanner/ui/main_window.py`
  - Define `AppState` enum: `IDLE`, `CAPTURING`, `SELECTING`, `SELECTED`, `PROCESSING`, `RESULT`
  - Define `MainWindow(QMainWindow)` class

- [x] **4.2 Implement `OCRWorker(QThread)`**
  - Signals: `finished(list)`, `error(str)`, `image_ready(object)`
  - `__init__`: store image and lang
  - `run()`: call `extract_text()`, then `draw_ocr_boxes()`, emit signals
  - Catch `OCRError`, emit `error` signal

- [x] **4.3 Implement `_setup_ui()`**
  - Create central widget with horizontal layout
  - Left: `Canvas` widget
  - Right: `QTextEdit` (read-only) for extracted text, "Copy to Clipboard" button
  - Top toolbar: `[Capture] [OCR] [Save] [Reset]` buttons
  - Status bar at bottom
  - Initially: OCR and Save buttons disabled

- [x] **4.4 Implement `_set_state()`**
  - Update button enabled states per state:
    - `IDLE`: Capture enabled, OCR/Save disabled
    - `SELECTING`: Capture enabled, OCR disabled
    - `SELECTED`: Capture enabled, OCR enabled, Save disabled
    - `PROCESSING`: All buttons disabled
    - `RESULT`: Capture enabled, OCR disabled, Save enabled
  - Update status bar message
  - Store current state in `self._state`

- [x] **4.5 Implement `_connect_signals()`**
  - Connect button clicks to handlers: `_on_capture`, `_on_ocr`, `_on_save`, `_on_reset`
  - Connect `canvas.region_selected` to `_on_region_selected`
  - Initialize `OCRWorker` and connect its signals: `finished`, `error`, `image_ready`

- [x] **4.6 Implement `_on_capture()`**
  - Set state to `CAPTURING`
  - Call `capture_screen()`
  - Convert PIL Image to QPixmap, call `canvas.set_image()`
  - Set state to `SELECTING`
  - On `ScreenCaptureError`: show `QMessageBox.critical`, set state to `IDLE`

- [x] **4.7 Implement `_on_region_selected(x, y, w, h)`**
  - Store selection coordinates in `self._selection`
  - Set state to `SELECTED` (enables OCR button)

- [x] **4.8 Implement `_on_ocr()`**
  - Set state to `PROCESSING`
  - Crop `self._screenshot` using stored selection coords
  - Create and start `OCRWorker` with cropped image
  - Disable buttons during processing

- [x] **4.9 Implement OCR worker signal handlers**
  - `_on_ocr_finished(blocks)`: populate `QTextEdit` with extracted text, set state to `RESULT`
  - `_on_ocr_image_ready(image)`: convert to QPixmap, call `canvas.set_image()` with annotated result
  - `_on_ocr_error(msg)`: show `QMessageBox.warning`, set state to `SELECTED`

- [x] **4.10 Implement `_on_save()`**
  - Open `QFileDialog.getSaveFileName()` for PNG
  - Save current canvas pixmap or annotated image
  - On `OSError`: show `QMessageBox.warning`

- [x] **4.11 Implement `_on_reset()`**
  - Clear canvas, clear text panel, reset selection
  - Set state to `IDLE`

- [x] **4.12 Implement "Copy to Clipboard" button handler**
  - Copy text from `QTextEdit` to `QApplication.clipboard()`

- [x] **4.13 Write unit tests (`tests/test_main_window.py`)**
  - Test state transitions: IDLE → SELECTING → SELECTED → RESULT → IDLE
  - Test button enabled states per state
  - Test `_on_capture()` with mocked `capture_screen()`
  - Test `_on_ocr()` with mocked `extract_text()`
  - Test error paths: capture failure, OCR failure
  - Test `OCRWorker` independently (no UI)

- [x] **4.14 Run tests and verify**
  - `pytest tests/test_main_window.py -v`
  - All tests pass
