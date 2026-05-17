# Module: `core/ocr.py` — Task List

> **Design Reference**: `doc/detailed-design.md` §3
> **Dependencies**: `pytesseract`, `Pillow`
> **Test Isolation**: Mock `pytesseract.image_to_data()`, no PyQt6 needed

## Tasks

- [x] **2.1 Create module skeleton**
  - Create `ocr_scanner/core/ocr.py`
  - Define `OCRError(Exception)` class
  - Define `TextBlock` dataclass with fields: `text`, `x`, `y`, `w`, `h`, `confidence`
  - Add confidence property methods: `is_high_confidence`, `is_medium_confidence`, `is_low_confidence`

- [x] **2.2 Implement `extract_text()`**
  - Call `pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)`
  - Iterate over dict entries, filter out empty text and `conf <= 0`
  - Build and return `list[TextBlock]`
  - Wrap in try/except, raise `OCRError` on failure

- [x] **2.3 Implement `draw_ocr_boxes()`**
  - Copy image and convert to RGB
  - Use `ImageDraw.Draw` to draw rectangles
  - Color scheme: green (>80%), yellow (50-80%), red (<=50%)
  - Return new annotated image (original unchanged)

- [x] **2.4 Implement `validate_tesseract()`**
  - Use `pytesseract.get_tesseract_version()` or `shutil.which("tesseract")`
  - Return `True` if available, `False` otherwise
  - Handle exceptions gracefully (no crash)

- [x] **2.5 Write unit tests (`tests/test_ocr.py`)**
  - Test `TextBlock` confidence properties with boundary values (80.0, 50.0, 0.0, 100.0)
  - Test `extract_text()` with mocked `pytesseract.image_to_data()` returning synthetic dict
  - Test `extract_text()` filters empty strings and `conf <= 0` entries
  - Test `OCRError` is raised when pytesseract fails
  - Test `draw_ocr_boxes()` draws correct colors at expected pixel coordinates
  - Test `validate_tesseract()` returns bool without crashing

- [x] **2.6 Run tests and verify**
  - `pytest tests/test_ocr.py -v`
  - All tests pass
