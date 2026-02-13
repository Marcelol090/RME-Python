"""Application splash screen with progress feedback.

Uses QSplashScreen with a programmatically generated gradient pixmap
and styled text overlay. Shows startup phases (loading assets,
initializing plugins, etc.) before the main window appears.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPixmap,
)
from PyQt6.QtWidgets import QApplication, QSplashScreen, QWidget

from py_rme_canary.vis_layer.ui.theme import get_theme_manager

_SPLASH_WIDTH = 520
_SPLASH_HEIGHT = 320


def _create_splash_pixmap() -> QPixmap:
    """Generate a gradient splash image programmatically."""
    pixmap = QPixmap(_SPLASH_WIDTH, _SPLASH_HEIGHT)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    tm = get_theme_manager()
    c = tm.tokens["color"]
    # Fallback to hardcoded if tokens fail or are missing (safety)
    primary_surface = c["surface"].get("primary", "#0F172A")
    secondary_surface = c["surface"].get("secondary", "#1E293B")
    accent_color = c["brand"].get("primary", "#2DD4BF")
    text_color = c["text"].get("primary", "#F1F5F9")
    sub_text_color = c["text"].get("secondary", "#94A3B8")

    # Background gradient
    grad = QLinearGradient(0, 0, 0, _SPLASH_HEIGHT)
    grad.setColorAt(0.0, QColor(secondary_surface))
    grad.setColorAt(0.5, QColor(primary_surface))
    grad.setColorAt(1.0, QColor(c["surface"].get("elevated", "#020617")))

    painter.setBrush(grad)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, _SPLASH_WIDTH, _SPLASH_HEIGHT, 16, 16)

    # Accent line (Teal/Green gradient for Noct theme)
    accent_grad = QLinearGradient(0, 0, _SPLASH_WIDTH, 0)
    accent_grad.setColorAt(0.0, QColor(accent_color))
    accent_grad.setColorAt(0.5, QColor(c["brand"].get("secondary", "#14B8A6")))
    accent_grad.setColorAt(1.0, QColor(c["brand"].get("active", "#5EEAD4")))

    painter.setBrush(accent_grad)
    painter.drawRect(0, _SPLASH_HEIGHT - 4, _SPLASH_WIDTH, 4)

    # Title
    title_font = QFont("Segoe UI", 22, QFont.Weight.Bold)
    painter.setFont(title_font)
    painter.setPen(QColor(text_color))
    painter.drawText(40, 80, "Canary Map Editor")

    # Subtitle
    sub_font = QFont("Segoe UI", 11)
    painter.setFont(sub_font)
    painter.setPen(QColor(sub_text_color))

    try:
        from py_rme_canary.core.version import get_build_info
        info = get_build_info()
        version_text = f"v{info.semver}"
        if info.commit_hash:
            version_text += f" ({info.commit_hash})"
    except Exception:
        version_text = ""
    painter.drawText(42, 106, version_text)

    # Decorative Canary icon (simple shape) - using accent color with transparency
    painter.setPen(Qt.PenStyle.NoPen)

    # Parse accent color to get RGBA for transparency
    base_accent = QColor(accent_color)

    # Outer circle
    outer_color = QColor(base_accent)
    outer_color.setAlpha(40)
    painter.setBrush(outer_color)
    painter.drawEllipse(380, 40, 100, 100)

    # Inner circle
    inner_color = QColor(base_accent)
    inner_color.setAlpha(20)
    painter.setBrush(inner_color)
    painter.drawEllipse(360, 60, 140, 140)

    painter.end()
    return pixmap


class StartupSplash(QSplashScreen):
    """Splash screen shown during application startup.

    Usage::

        splash = StartupSplash()
        splash.show()
        app.processEvents()
        splash.set_phase("Loading assets...")
        # ... do work ...
        splash.finish(main_window)
    """

    def __init__(self) -> None:
        pixmap = _create_splash_pixmap()
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self._phase = ""
        self._progress = 0
        self._total = 0

    def set_phase(self, text: str, *, progress: int = 0, total: int = 0) -> None:
        """Update the status message and optional progress."""
        self._phase = text
        self._progress = progress
        self._total = total

        tm = get_theme_manager()
        accent = tm.tokens["color"]["brand"]["primary"]

        self.showMessage(
            self._format_message(),
            int(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft),
            QColor(accent),
        )
        app = QApplication.instance()
        if app is not None:
            app.processEvents()

    def _format_message(self) -> str:
        msg = f"  {self._phase}"
        if self._total > 0:
            pct = int((self._progress / self._total) * 100)
            msg += f" ({pct}%)"
        return msg

    def finish_with_delay(self, main_win: QWidget, delay_ms: int = 400) -> None:
        """Close the splash after a brief delay once the main window shows."""
        QTimer.singleShot(delay_ms, lambda: self.finish(main_win))
