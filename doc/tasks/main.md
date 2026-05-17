# Module: `main.py` — Task List

> **Design Reference**: `doc/detailed-design.md` §6
> **Dependencies**: All modules
> **Test Isolation**: Integration-level, manual or end-to-end with mocks

## Tasks

- [x] **5.1 Create entry point**
  - Create `ocr_scanner/main.py`
  - Add `if __name__ == "__main__":` guard

- [x] **5.2 Implement `main()` function**
  - Create `QApplication(sys.argv)`
  - Set application name and version
  - Call `validate_tesseract()` pre-flight check
  - If Tesseract missing: show `QMessageBox.critical` with install instructions, `sys.exit(1)`
  - Create `MainWindow()`, call `show()`
  - Run `sys.exit(app.exec())`

- [x] **5.3 Create `requirements.txt`**
  - List: `PyQt6`, `mss`, `pytesseract`, `Pillow`, `pytest`, `pytest-qt`

- [x] **5.4 Manual smoke test**
  - Activate venv, run `python ocr_scanner/main.py`
  - Verify window opens with placeholder text
  - Verify Tesseract pre-flight works (test with and without Tesseract installed)
