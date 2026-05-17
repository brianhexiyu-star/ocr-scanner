# Module: `core/capture.py` — Task List

> **Design Reference**: `doc/detailed-design.md` §2
> **Dependencies**: `mss`, `Pillow`
> **Test Isolation**: Mock `mss.mss()`, no PyQt6 needed

## Tasks

- [x] **1.1 Create module skeleton**
  - Create `ocr_scanner/core/__init__.py` (empty)
  - Create `ocr_scanner/core/capture.py`
  - Define `ScreenCaptureError(Exception)` class
  - Add docstrings matching the design spec

- [x] **1.2 Implement `capture_screen()`**
  - Use `mss.mss()` context manager
  - Grab `sct.monitors[monitor]`
  - Convert BGRA bytes to PIL Image via `Image.frombytes("RGB", ..., "raw", "BGRX")`
  - Wrap in try/except, raise `ScreenCaptureError` on failure

- [x] **1.3 Implement `get_monitor_count()`**
  - Use `mss.mss()` to access `sct.monitors`
  - Return `len(sct.monitors) - 1` (index 0 is combined, 1-based monitors follow)

- [x] **1.4 Write unit tests (`tests/test_capture.py`)**
  - Test `capture_screen()` returns valid PIL Image with mocked `mss`
  - Test `ScreenCaptureError` is raised when `mss.grab()` raises
  - Test `get_monitor_count()` returns correct count with mocked monitors
  - Verify image mode is "RGB" and size matches mock data

- [x] **1.5 Run tests and verify**
  - `pytest tests/test_capture.py -v`
  - All tests pass
