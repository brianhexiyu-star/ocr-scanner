"""Screen capture module — captures the full screen at native pixel resolution."""

from __future__ import annotations

import mss
from PIL import Image


class ScreenCaptureError(Exception):
    """Raised when screen capture fails."""

    pass


def capture_screen(monitor: int = 1) -> Image.Image:
    """
    Capture the specified monitor at native resolution.

    Args:
        monitor: Monitor index (1-based). 0 = all monitors combined.

    Returns:
        PIL.Image.Image in RGB mode.

    Raises:
        ScreenCaptureError: If mss fails to capture (no display, permission denied).
    """
    try:
        with mss.mss() as sct:
            monitor_data = sct.grab(sct.monitors[monitor])
            image = Image.frombytes("RGB", monitor_data.size, monitor_data.bgra, "raw", "BGRX")
            return image
    except Exception as e:
        raise ScreenCaptureError(f"Failed to capture screen: {e}") from e


def get_monitor_count() -> int:
    """
    Return the number of available monitors.

    Returns:
        int >= 1
    """
    with mss.mss() as sct:
        return len(sct.monitors) - 1
