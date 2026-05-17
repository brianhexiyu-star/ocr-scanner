"""Unit tests for ocr_scanner.ui.canvas module."""

from __future__ import annotations

import pytest
from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QRubberBand
from pytestqt.exceptions import TimeoutError

from ocr_scanner.ui.canvas import Canvas


class TestCanvasInit:
    """Tests for Canvas initialization."""

    def test_init_sets_internal_state_to_none(self, qtbot) -> None:
        """Verify all internal state attributes start as None."""
        canvas = Canvas()
        qtbot.addWidget(canvas)

        assert canvas._pixmap is None
        assert canvas._scaled_pixmap is None
        assert canvas._rubber_band is None
        assert canvas._origin is None
        assert canvas._selection_rect is None

    def test_init_has_minimum_size(self, qtbot) -> None:
        """Verify canvas has a minimum size set."""
        canvas = Canvas()
        qtbot.addWidget(canvas)

        assert canvas.minimumWidth() >= 400
        assert canvas.minimumHeight() >= 300


class TestSetImage:
    """Tests for Canvas.set_image()."""

    def test_set_image_stores_pixmap(self, qtbot) -> None:
        """set_image() stores the original pixmap."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        pixmap = QPixmap(1920, 1080)
        pixmap.fill(Qt.GlobalColor.white)

        canvas.set_image(pixmap)

        assert canvas._pixmap is not None
        assert canvas._pixmap.width() == 1920
        assert canvas._pixmap.height() == 1080

    def test_set_image_creates_scaled_pixmap(self, qtbot) -> None:
        """set_image() creates a scaled pixmap fitting the widget."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        pixmap = QPixmap(1920, 1080)
        pixmap.fill(Qt.GlobalColor.white)

        canvas.set_image(pixmap)

        assert canvas._scaled_pixmap is not None
        # Scaled pixmap should fit within widget bounds
        assert canvas._scaled_pixmap.width() <= 800
        assert canvas._scaled_pixmap.height() <= 600

    def test_set_image_clears_selection(self, qtbot) -> None:
        """set_image() clears any existing selection."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        # Simulate a selection
        canvas._selection_rect = QRect(10, 10, 100, 100)

        pixmap = QPixmap(1920, 1080)
        pixmap.fill(Qt.GlobalColor.white)
        canvas.set_image(pixmap)

        assert canvas._selection_rect is None

    def test_set_image_triggers_repaint(self, qtbot) -> None:
        """set_image() triggers a repaint via update()."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        pixmap = QPixmap(1920, 1080)
        pixmap.fill(Qt.GlobalColor.white)

        # After set_image, _scaled_pixmap should be set (indicating update path)
        canvas.set_image(pixmap)
        assert canvas._scaled_pixmap is not None


class TestWidgetToImageCoords:
    """Tests for Canvas._widget_to_image_coords()."""

    def test_returns_zero_when_no_pixmap(self, qtbot) -> None:
        """Returns (0, 0, 0, 0) when no pixmap is set."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)

        rect = QRect(10, 10, 100, 50)
        result = canvas._widget_to_image_coords(rect)

        assert result == (0, 0, 0, 0)

    def test_scales_with_known_ratio_1920x1080_in_800x600(self, qtbot) -> None:
        """Correctly scales coordinates for 1920px image in 800x600 widget.

        1920x1080 scaled to 800x600 with KeepAspectRatio → 800x450.
        Centered vertically: offset_y = (600 - 450) // 2 = 75, offset_x = 0.
        scale_x = 1920/800 = 2.4, scale_y = 1080/450 = 2.4.
        """
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        pixmap = QPixmap(1920, 1080)
        pixmap.fill(Qt.GlobalColor.white)
        canvas.set_image(pixmap)

        # Verify scaled pixmap dimensions
        assert canvas._scaled_pixmap is not None
        assert canvas._scaled_pixmap.width() == 800
        assert canvas._scaled_pixmap.height() == 450

        # Widget rect: x=100, y=100 (75 offset + 25 into image), w=200, h=100
        rect = QRect(100, 100, 200, 100)
        result = canvas._widget_to_image_coords(rect)

        # offset_x=0, offset_y=75, scale=2.4
        # x = (100 - 0) * 2.4 = 240
        # y = (100 - 75) * 2.4 = 60
        # w = 200 * 2.4 = 480
        # h = 100 * 2.4 = 240
        assert result == (240, 60, 480, 240)

    def test_scales_with_1x1_ratio(self, qtbot) -> None:
        """Correctly handles 1:1 scale ratio."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(500, 500)
        canvas.show()

        pixmap = QPixmap(500, 500)
        pixmap.fill(Qt.GlobalColor.white)
        canvas.set_image(pixmap)

        # 1:1 ratio, no letterboxing
        rect = QRect(50, 50, 100, 100)
        result = canvas._widget_to_image_coords(rect)

        assert result == (50, 50, 100, 100)

    def test_scales_with_large_image(self, qtbot) -> None:
        """Correctly handles large image with letterboxing on both axes."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(400, 400)
        canvas.show()

        # 2000x1000 image in 400x400 widget → scaled to 400x200
        # offset_x=0, offset_y=(400-200)//2=100
        pixmap = QPixmap(2000, 1000)
        pixmap.fill(Qt.GlobalColor.white)
        canvas.set_image(pixmap)

        assert canvas._scaled_pixmap is not None
        assert canvas._scaled_pixmap.width() == 400
        assert canvas._scaled_pixmap.height() == 200

        # Click at widget (0, 150) → image y = (150-100) * (1000/200) = 250
        rect = QRect(0, 150, 200, 50)
        result = canvas._widget_to_image_coords(rect)

        # scale_x = 2000/400 = 5.0, scale_y = 1000/200 = 5.0
        # x = (0-0)*5 = 0, y = (150-100)*5 = 250
        # w = 200*5 = 1000, h = 50*5 = 250
        assert result == (0, 250, 1000, 250)


class TestMouseDrag:
    """Tests for mouse drag selection."""

    def test_mouse_drag_emits_region_selected(self, qtbot) -> None:
        """Mouse drag emits region_selected with correct scaled coordinates."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        pixmap = QPixmap(1920, 1080)
        pixmap.fill(Qt.GlobalColor.white)
        canvas.set_image(pixmap)

        with qtbot.waitSignal(canvas.region_selected) as blocker:
            qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
            qtbot.mouseMove(canvas, pos=QPoint(300, 250))
            qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPoint(300, 250))

        # 1920x1080 in 800x600 → scaled to 800x450, offset_y=75
        # scale_x = 1920/800 = 2.4, scale_y = 1080/450 = 2.4
        # Drag (100,100)→(300,250): rect=(100,100,200,150)
        # x = (100-0)*2.4 = 240, y = (100-75)*2.4 = 60
        # w = 200*2.4 = 480, h = 150*2.4 = 360
        x, y, w, h = blocker.args
        assert abs(x - 240) <= 5
        assert abs(y - 60) <= 5
        assert abs(w - 480) <= 5
        assert abs(h - 360) <= 5

    def test_small_drag_does_not_emit_signal(self, qtbot) -> None:
        """Small drags (< 5px) do NOT emit region_selected."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        pixmap = QPixmap(1920, 1080)
        pixmap.fill(Qt.GlobalColor.white)
        canvas.set_image(pixmap)

        # Use a small drag (3x3 pixels)
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
        qtbot.mouseMove(canvas, pos=QPoint(103, 103))

        with pytest.raises(
            TimeoutError,
            match="Signal region_selected.*not emitted",
        ):
            with qtbot.waitSignal(canvas.region_selected, timeout=500):
                qtbot.mouseRelease(
                    canvas, Qt.MouseButton.LeftButton, pos=QPoint(103, 103)
                )

    def test_mouse_drag_creates_rubber_band(self, qtbot) -> None:
        """Mouse drag creates a QRubberBand."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        pixmap = QPixmap(1920, 1080)
        pixmap.fill(Qt.GlobalColor.white)
        canvas.set_image(pixmap)

        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))

        assert canvas._rubber_band is not None
        assert isinstance(canvas._rubber_band, QRubberBand)
        assert canvas._rubber_band.isVisible()

    def test_mouse_drag_stores_selection_rect(self, qtbot) -> None:
        """Mouse drag stores the selection rect in widget coordinates."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        pixmap = QPixmap(1920, 1080)
        pixmap.fill(Qt.GlobalColor.white)
        canvas.set_image(pixmap)

        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
        qtbot.mouseMove(canvas, pos=QPoint(300, 250))
        qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPoint(300, 250))

        assert canvas._selection_rect is not None
        # Allow ±2 pixel tolerance for Qt rubber band off-by-one
        assert abs(canvas._selection_rect.x() - 100) <= 2
        assert abs(canvas._selection_rect.y() - 100) <= 2
        assert abs(canvas._selection_rect.width() - 200) <= 2
        assert abs(canvas._selection_rect.height() - 150) <= 2

    def test_mouse_press_without_pixmap_does_nothing(self, qtbot) -> None:
        """Mouse press without pixmap set does not create rubber band."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))

        assert canvas._rubber_band is None
        assert canvas._origin is None


class TestClear:
    """Tests for Canvas.clear()."""

    def test_clear_resets_pixmap(self, qtbot) -> None:
        """clear() resets pixmap to None."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        pixmap = QPixmap(1920, 1080)
        pixmap.fill(Qt.GlobalColor.white)
        canvas.set_image(pixmap)

        assert canvas._pixmap is not None
        canvas.clear()
        assert canvas._pixmap is None

    def test_clear_resets_scaled_pixmap(self, qtbot) -> None:
        """clear() resets scaled pixmap to None."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        pixmap = QPixmap(1920, 1080)
        pixmap.fill(Qt.GlobalColor.white)
        canvas.set_image(pixmap)

        assert canvas._scaled_pixmap is not None
        canvas.clear()
        assert canvas._scaled_pixmap is None

    def test_clear_resets_selection(self, qtbot) -> None:
        """clear() resets selection state."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        canvas._selection_rect = QRect(10, 10, 100, 100)
        canvas._origin = QPoint(50, 50)

        canvas.clear()

        assert canvas._selection_rect is None
        assert canvas._origin is None

    def test_clear_shows_placeholder(self, qtbot) -> None:
        """clear() results in placeholder being shown (no pixmap)."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        pixmap = QPixmap(1920, 1080)
        pixmap.fill(Qt.GlobalColor.white)
        canvas.set_image(pixmap)
        canvas.clear()

        # After clear, no pixmap means placeholder text is drawn
        assert canvas._pixmap is None
        assert canvas._scaled_pixmap is None


class TestGetSelection:
    """Tests for Canvas.get_selection()."""

    def test_get_selection_returns_none_when_no_selection(self, qtbot) -> None:
        """get_selection() returns None when no selection exists."""
        canvas = Canvas()
        qtbot.addWidget(canvas)

        assert canvas.get_selection() is None

    def test_get_selection_returns_image_coords(self, qtbot) -> None:
        """get_selection() returns coordinates in image pixel space."""
        canvas = Canvas()
        qtbot.addWidget(canvas)
        canvas.resize(800, 600)
        canvas.show()

        pixmap = QPixmap(1920, 1080)
        pixmap.fill(Qt.GlobalColor.white)
        canvas.set_image(pixmap)

        # Set a widget-space selection
        canvas._selection_rect = QRect(100, 100, 200, 150)

        result = canvas.get_selection()

        assert result is not None
        # 1920x1080 in 800x600 → scaled 800x450, offset_y=75, scale=2.4
        # x=(100-0)*2.4=240, y=(100-75)*2.4=60, w=480, h=360
        assert result == (240, 60, 480, 360)


class TestSelectionCleared:
    """Tests for selection_cleared signal."""

    def test_selection_cleared_signal_exists(self, qtbot) -> None:
        """Verify selection_cleared signal is defined."""
        canvas = Canvas()
        qtbot.addWidget(canvas)

        assert hasattr(canvas, "selection_cleared")
