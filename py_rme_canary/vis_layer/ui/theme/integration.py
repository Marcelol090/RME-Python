"""Theme integration helper for applying modern theme to the application.

Provides easy integration with existing QtMapEditor using the centralized ThemeManager.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

# Use the centralized ThemeManager from __init__.py
from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QApplication, QMainWindow

logger = logging.getLogger(__name__)


def apply_modern_theme(app: QApplication) -> bool:
    """Apply the current theme (defaulting to Noct/Dark) to the entire application.

    Args:
        app: QApplication instance

    Returns:
        True if theme was applied successfully
    """
    try:
        tm = get_theme_manager()
        tm.apply_theme() # This applies the stylesheet using current tokens

        logger.info(f"Modern theme ({tm.current_theme}) applied successfully")
        return True

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
    """Apply additional window-specific theming using current tokens.

    Args:
        window: Main window to style
    """
    try:
        tm = get_theme_manager()
        c = tm.tokens["color"]

        # Set window background explicitly if needed, though global stylesheet handles QWidget
        window.setStyleSheet(f"""
            QMainWindow {{
                background-color: {c["surface"]["primary"]};
            }}
        """)

        # Set minimum size for good UX
        window.setMinimumSize(1024, 768)

        logger.debug("Window theme applied")

    except Exception as e:
        logger.warning(f"Window theming failed: {e}")

# Re-export ThemeManager for backward compatibility if needed,
# but preferably users should import from . directly
