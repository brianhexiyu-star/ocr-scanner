# Module: `ui/canvas.py` — Task List

> **Design Reference**: `doc/detailed-design.md` §4
> **Dependencies**: `PyQt6`
> **Test Isolation**: `pytest-qt`, synthetic QPixmap, mock `QRubberBand` if needed

## Tasks

- [x] **3.1 Create module skeleton**
  - Create `ocr_scanner/ui/__init__.py` (empty)
  - Create `ocr_scanner/ui/canvas.py`
  - Define `Canvas(QWidget)` class
  - Define signals: `region_selected = pyqtSignal(int, int, int, int)`, `selection_cleared = pyqtSignal()`

- [x] **3.2 Implement `__init__` and internal state**
  - Initialize: `_pixmap`, `_scaled_pixmap`, `_rubber_band`, `_origin`, `_selection_rect` to `None`
  - Set minimum size for the widget
  - Enable mouse tracking if needed

- [x] **3.3 Implement `set_image()`**
  - Store original pixmap in `_pixmap`
  - Scale pixmap to fit widget size, store in `_scaled_pixmap`
  - Clear any existing selection and rubber band
  - Call `update()` to trigger repaint

- [x] **3.4 Implement `clear()`**
  - Reset all internal state to `None`
  - Set placeholder text (e.g., "Click 'Capture' to start")
  - Call `update()`

- [x] **3.5 Implement `get_selection()`**
  - If `_selection_rect` exists, convert to image coords via `_widget_to_image_coords()` and return tuple
  - Otherwise return `None`

- [x] **3.6 Implement `_widget_to_image_coords()`**
  - Calculate `scale_x = _pixmap.width() / self.width()`
  - Calculate `scale_y = _pixmap.height() / self.height()`
  - Apply scales to rect x, y, width, height
  - Return `(int(x), int(y), int(w), int(h))`

- [x] **3.7 Implement mouse event handlers**
  - `mousePressEvent`: on left click with pixmap set, create/show `QRubberBand`, store origin
  - `mouseMoveEvent`: update rubber band geometry with normalized rect
  - `mouseReleaseEvent`: if rect > 5x5 px, store selection, emit `region_selected` with image coords; reset origin

- [x] **3.8 Implement `paintEvent()`**
  - If `_scaled_pixmap` exists, draw it centered in the widget
  - If no pixmap, draw placeholder text centered

- [x] **3.9 Write unit tests (`tests/test_canvas.py`)**
  - Test `set_image()` stores pixmap and triggers repaint (use `pytest-qt`)
  - Test `_widget_to_image_coords()` with known scale ratios (e.g., 1920px image in 800px widget)
  - Test mouse drag emits `region_selected` with correct scaled coordinates
  - Test small drags (< 5px) do NOT emit signal
  - Test `clear()` resets state and shows placeholder
  - Test `selection_cleared` signal on double-click (if implemented)

- [x] **3.10 Run tests and verify**
  - `pytest tests/test_canvas.py -v`
  - All tests pass
