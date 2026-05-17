# OCR Scanner — Progress Tracker

> Update checklists as modules are completed.

## Module Status

- [x] **`core/capture`** — Screen capture via mss
  - Task file: `doc/tasks/capture.md`
  - Status: Complete (13 tests passing)

- [x] **`core/ocr`** — OCR processing via pytesseract
  - Task file: `doc/tasks/ocr.md`
  - Status: Complete (26 tests passing)

- [x] **`ui/canvas`** — Image display + region selection widget
  - Task file: `doc/tasks/canvas.md`
  - Status: Complete (22 tests passing)

- [x] **`ui/main_window`** — Main window, orchestration, state machine
  - Task file: `doc/tasks/main_window.md`
  - Status: Complete (38 tests passing)

- [x] **`main`** — Entry point, pre-flight checks
  - Task file: `doc/tasks/main.md`
  - Status: Complete

## Recommended Execution Order

1. `core/capture` — No dependencies, pure logic
2. `core/ocr` — No dependencies, pure logic (can run in parallel with capture)
3. `ui/canvas` — Depends only on PyQt6 (can run in parallel with core modules)
4. `ui/main_window` — Depends on all above
5. `main` — Depends on everything, final integration

## Overall Progress

- **Modules completed**: 5 / 5
- **Tests passing**: 5 / 5 (99 tests total)
- **mypy**: Clean (0 errors)
- **ruff**: Clean (0 violations)
