# OCR Scanner — Project Proposal

## Overview

OCR Scanner is a PyQt6 desktop application that captures the screen, lets the user select a region, runs OCR on it, and displays the extracted text with visual bounding boxes.

This module serves as the **message viewing component** of a larger cross-platform chatbot application. It provides the UI and OCR pipeline for extracting text from screen content. Future iterations will integrate a chat agent API to enable interactive conversations based on the extracted text.

## Architecture

```
ocr_scanner/
├── main.py              # Entry point
├── core/
│   ├── capture.py       # Screen capture via mss
│   └── ocr.py           # OCR via pytesseract
└── ui/
    ├── main_window.py   # Main window, controls, orchestration
    └── canvas.py        # Custom widget: display + region selection
```

## User Workflow

| Step | Action | Description |
|------|--------|-------------|
| 1 | **Launch** | Window opens with placeholder "Click 'Capture' to start" |
| 2 | **Capture Screen** | Click button → `mss` grabs full screen at native resolution → PIL Image stored in `self.screenshot` → converted to QPixmap → displayed in canvas (scaled to fit widget) |
| 3 | **Select Region** | User drags mouse on canvas → rubber band rectangle appears → on release, widget coords are scaled back to native image coords → `region_selected` signal emits `(x, y, w, h)` |
| 4 | **Confirm & OCR** | Button enables after selection → crops region from `self.screenshot` PIL image → passes crop to `OCRWorker` (background `QThread`) → runs `pytesseract.image_to_data()` → returns list of `TextBlock` (text, bbox, confidence) |
| 5 | **Display Results** | `draw_ocr_boxes()` renders colored rectangles on the cropped image (green >80%, yellow 50-80%, red <50%) → result shown in canvas → extracted text shown in side panel → save button enables |
| 6 | **Save** | Saves the annotated image as PNG |
| 7 | **Reset** | Clears everything, returns to idle state |

## Key Technical Details

- **Screen capture**: `mss` library, captures at native pixel resolution (Retina-aware)
- **OCR engine**: Tesseract 5 via `pytesseract`, word-level output with confidence scores
- **UI framework**: PyQt6, custom `QWidget` canvas with `QRubberBand` for selection
- **Threading**: `QThread` for OCR to avoid freezing UI during processing
- **Coordinate scaling**: Widget coords → image coords via `pixmap.width / widget.width` ratio
- **State machine**: `idle` → `selecting` → `selected` → `result`

## Environment Setup

### Prerequisites

- Python 3.10+
- Tesseract OCR engine installed on the system

### Install Tesseract

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt install tesseract-ocr
```

**Windows:**
Download installer from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.

### Virtual Environment & Dependencies

```bash
# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows

# Install Python dependencies
pip install PyQt6 mss pytesseract Pillow
```

### Verify Installation

```bash
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

## Test Plan

### Unit Tests

| Module | Test Cases |
|--------|-----------|
| `core/capture.py` | Screen capture returns valid PIL Image; handles multi-monitor setups; handles Retina/HiDPI scaling |
| `core/ocr.py` | OCR returns `TextBlock` list with correct fields; handles empty images; handles low-confidence results; surfaces errors instead of failing silently |
| `ui/canvas.py` | Mouse drag creates rubber band; coordinate scaling is accurate; region selection emits correct signal |

### Integration Tests

- Full workflow: capture → select → OCR → display results → save
- State transitions: idle → selecting → selected → result → reset → idle
- OCRWorker threading: UI remains responsive during OCR processing

### Manual Test Checklist

- [ ] Launch app, verify placeholder text displays
- [ ] Capture screen on single and multi-monitor setups
- [ ] Select region, verify bounding box matches selection
- [ ] Run OCR on text-heavy and image-heavy regions
- [ ] Verify confidence color coding (green/yellow/red)
- [ ] Save annotated image, verify PNG output
- [ ] Reset clears all state correctly
- [ ] OCR errors display user-friendly messages (not silent failures)

### Test Structure

```
ocr_scanner/
├── tests/
│   ├── test_capture.py
│   ├── test_ocr.py
│   ├── test_canvas.py
│   └── test_integration.py
```

Run tests with:
```bash
pip install pytest
pytest tests/
```

## Known Issues & Risks

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Screenshot displays scaled down in widget | Retina images squeezed into ~800px canvas, visual quality loss | Consider scrollable native-size view or higher DPI pixmap handling |
| OCR may fail silently | User sees no output, no feedback on what went wrong | Add debug logging and user-facing error messages; validate Tesseract binary path on startup |
| Tesseract not installed | App crashes on import or OCR call | Pre-flight check for `tesseract` binary, show install instructions if missing |
| Cross-platform differences | macOS Retina, Windows DPI scaling, Linux display servers | Abstract DPI handling; test on each target platform |

## Future Work

- **Chat Agent API Integration**: Connect extracted text to a chat agent backend for interactive Q&A
- **Multi-language OCR**: Support language selection and mixed-language text
- **Batch Processing**: OCR multiple regions or full-page capture
- **Export Formats**: Export extracted text as TXT, Markdown, or JSON
- **Clipboard Integration**: One-click copy of OCR results to clipboard
- **History**: Store and browse previous OCR sessions
