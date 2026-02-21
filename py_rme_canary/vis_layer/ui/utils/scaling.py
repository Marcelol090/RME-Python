"""Scaling utilities for UI components."""

from PyQt6.QtWidgets import QApplication, QWidget


def scale_dip(widget: QWidget, value: int) -> int:
    """Scale a value based on the screen DPI.

    Args:
        widget: The widget context for determining the screen.
        value: The base value in DIP (Device Independent Pixels).

    Returns:
        The scaled pixel value.
    """
    app = QApplication.instance()
    if app is None:
        return int(value)
    screen = widget.screen() or app.primaryScreen()
    if screen is None:
        return int(value)
    factor = float(screen.logicalDotsPerInch()) / 96.0
    return max(1, int(round(float(value) * max(1.0, factor))))
