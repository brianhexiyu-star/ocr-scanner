"""Custom widget: display images and handle mouse-based region selection."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QPainter, QPaintEvent, QPixmap
from PyQt6.QtWidgets import QRubberBand, QWidget


class Canvas(QWidget):
    """Display images (screenshot or OCR result) and handle mouse-based region selection.

    Converts widget coordinates to image coordinates and emits selection events.
    """

    # Emitted when user finishes drawing a selection rectangle.
    # Coordinates are in native image pixel space (not widget space).
    region_selected = pyqtSignal(int, int, int, int)  # x, y, w, h

    # Emitted when user double-clicks to clear selection.
    selection_cleared = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self._scaled_pixmap: QPixmap | None = None
        self._rubber_band: QRubberBand | None = None
        self._origin: QPoint | None = None
        self._selection_rect: QRect | None = None
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)

    def set_image(self, pixmap: QPixmap) -> None:
        """Display a pixmap in the canvas, scaled to fit.

        Stores the original pixmap for coordinate conversion.
        Clears any existing selection.

        Args:
            pixmap: QPixmap to display.
        """
        self._pixmap = pixmap
        self._scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._clear_selection()
        self.update()

    def clear(self) -> None:
        """Reset canvas to empty state with placeholder text."""
        self._pixmap = None
        self._scaled_pixmap = None
        self._clear_selection()
        self.update()

    def get_selection(self) -> tuple[int, int, int, int] | None:
        """Return the current selection in image coordinates, or None.

        Returns:
            (x, y, w, h) in image pixel space, or None if no selection.
        """
        if self._selection_rect is None:
            return None
        return self._widget_to_image_coords(self._selection_rect)

    def _widget_to_image_coords(self, rect: QRect) -> tuple[int, int, int, int]:
        """Convert widget-space rectangle to image-space coordinates.

        Accounts for letterboxing: the scaled pixmap is centered in the
        widget with padding on the sides or top/bottom (KeepAspectRatio).

        Returns:
            (x, y, w, h) in image pixel space.
        """
        if not self._pixmap or not self._scaled_pixmap:
            return (0, 0, 0, 0)

        # Offset where the scaled pixmap is drawn (centering in paintEvent)
        offset_x = (self.width() - self._scaled_pixmap.width()) // 2
        offset_y = (self.height() - self._scaled_pixmap.height()) // 2

        # Scale based on the actual scaled pixmap size, not the widget size
        scale_x = self._pixmap.width() / self._scaled_pixmap.width()
        scale_y = self._pixmap.height() / self._scaled_pixmap.height()

        return (
            int((rect.x() - offset_x) * scale_x),
            int((rect.y() - offset_y) * scale_y),
            int(rect.width() * scale_x),
            int(rect.height() * scale_y),
        )

    def _clear_selection(self) -> None:
        """Clear selection state and hide rubber band."""
        if self._rubber_band:
            self._rubber_band.hide()
        self._selection_rect = None
        self._origin = None

    def paintEvent(self, event: QPaintEvent) -> None:  # type: ignore[override]  # noqa: N802
        """Draw the scaled pixmap or placeholder text."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._scaled_pixmap:
            # Center the scaled pixmap in the widget
            x = (self.width() - self._scaled_pixmap.width()) // 2
            y = (self.height() - self._scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, self._scaled_pixmap)
        else:
            # Draw placeholder text
            painter.drawText(
                self.rect(),
                int(Qt.AlignmentFlag.AlignCenter),
                "Click 'Capture' to start",
            )

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]  # noqa: N802
        """Handle mouse press: start rubber band selection."""
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and self._pixmap:
            self._origin = event.pos()
            if not self._rubber_band:
                self._rubber_band = QRubberBand(
                    QRubberBand.Shape.Rectangle, self
                )
            self._rubber_band.setGeometry(QRect(self._origin, QSize()))
            self._rubber_band.show()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]  # noqa: N802
        """Handle mouse move: update rubber band geometry."""
        super().mouseMoveEvent(event)
        if self._origin and self._rubber_band:
            self._rubber_band.setGeometry(
                QRect(self._origin, event.pos()).normalized()
            )

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]  # noqa: N802
        """Handle mouse release: emit selection if large enough."""
        super().mouseReleaseEvent(event)
        if self._origin and self._rubber_band:
            rect = self._rubber_band.geometry()
            if rect.width() > 5 and rect.height() > 5:
                self._selection_rect = rect
                img_coords = self._widget_to_image_coords(rect)
                self.region_selected.emit(*img_coords)
            self._origin = None
