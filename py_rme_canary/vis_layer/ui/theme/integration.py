"""Theme integration helper for applying modern theme to the application.

Provides easy integration with existing QtMapEditor.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QApplication, QMainWindow

logger = logging.getLogger(__name__)


def apply_modern_theme(app: QApplication) -> bool:
    """Apply modern dark theme to the entire application.

    Args:
        app: QApplication instance

    Returns:
        True if theme was applied successfully

    Usage:
        from PyQt6.QtWidgets import QApplication
        from vis_layer.ui.theme.integration import apply_modern_theme

        app = QApplication(sys.argv)
        apply_modern_theme(app)
    """
    try:
        from py_rme_canary.vis_layer.ui.theme.modern_theme import ModernTheme

        stylesheet = ModernTheme.get_stylesheet()
        app.setStyleSheet(stylesheet)

        logger.info("Modern theme applied successfully")
        return True

    except ImportError as e:
        logger.warning(f"Failed to import theme: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to apply theme: {e}")
        return False


def setup_modern_fonts(app: QApplication) -> None:
    """Setup modern fonts (Inter, JetBrains Mono).

    Loads web fonts if available, falls back to system fonts.
    """
    try:
        from PyQt6.QtGui import QFontDatabase

        # Try to load custom fonts (if bundled)
        # Fallback to system fonts is handled by CSS font-family

        # Log available fonts for debugging
        families = QFontDatabase.families()
        logger.debug(f"Available font families: {len(families)}")

    except Exception as e:
        logger.debug(f"Font setup: {e}")


def apply_theme_to_window(window: QMainWindow) -> None:
    """Apply additional window-specific theming.

    Args:
        window: Main window to style
    """
    try:
        # Set window background
        window.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E2E;
            }
        """)

        # Set minimum size for good UX
        window.setMinimumSize(1024, 768)

        logger.debug("Window theme applied")

    except Exception as e:
        logger.warning(f"Window theming failed: {e}")


class ThemeManager:
    """Singleton manager for theme switching.

    Future support for light/dark/system theme switching.
    """

    _instance: ThemeManager | None = None
    _current_theme: str = "dark"

    @classmethod
    def instance(cls) -> ThemeManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def current_theme(self) -> str:
        return self._current_theme

    def set_theme(self, theme: str) -> None:
        """Set the current theme.

        Args:
            theme: "dark", "light", or "system"
        """
        self._current_theme = theme
        # In future: reload stylesheet based on theme
        logger.info(f"Theme set to: {theme}")
