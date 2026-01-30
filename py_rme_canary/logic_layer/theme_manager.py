"""Theme Manager for RME.

Provides dark/light theme switching with stylesheet generation.

Layer: logic_layer (no PyQt6 imports)
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class ThemeMode(Enum):
    """Available theme modes."""

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"  # Follow OS preference


@dataclass
class ThemeColors:
    """Color scheme for a theme."""

    # Base colors
    background: str
    foreground: str
    surface: str
    border: str

    # Accent colors
    primary: str
    primary_hover: str
    secondary: str

    # Text colors
    text_primary: str
    text_secondary: str
    text_disabled: str

    # Status colors
    success: str
    warning: str
    error: str

    # Selection colors
    selection_bg: str
    selection_fg: str

    # Input colors
    input_bg: str
    input_border: str
    input_focus: str


# Predefined themes
LIGHT_THEME = ThemeColors(
    background="#f5f5f5",
    foreground="#ffffff",
    surface="#e0e0e0",
    border="#cccccc",
    primary="#2196f3",
    primary_hover="#1976d2",
    secondary="#757575",
    text_primary="#212121",
    text_secondary="#757575",
    text_disabled="#9e9e9e",
    success="#4caf50",
    warning="#ff9800",
    error="#f44336",
    selection_bg="#2196f3",
    selection_fg="#ffffff",
    input_bg="#ffffff",
    input_border="#cccccc",
    input_focus="#2196f3",
)

DARK_THEME = ThemeColors(
    background="#1e1e1e",
    foreground="#2d2d2d",
    surface="#383838",
    border="#555555",
    primary="#64b5f6",
    primary_hover="#42a5f5",
    secondary="#9e9e9e",
    text_primary="#e0e0e0",
    text_secondary="#a0a0a0",
    text_disabled="#606060",
    success="#81c784",
    warning="#ffb74d",
    error="#e57373",
    selection_bg="#1565c0",
    selection_fg="#ffffff",
    input_bg="#2d2d2d",
    input_border="#555555",
    input_focus="#64b5f6",
)


class ThemeManager:
    """Manages application theme switching.

    Usage:
        manager = get_theme_manager()
        manager.set_theme(ThemeMode.DARK)
        stylesheet = manager.get_stylesheet()
    """

    def __init__(self) -> None:
        self._mode: ThemeMode = ThemeMode.LIGHT
        self._on_theme_changed: list[Callable[[], None]] = []

    @property
    def mode(self) -> ThemeMode:
        return self._mode

    @property
    def colors(self) -> ThemeColors:
        """Get current theme colors."""
        if self._mode == ThemeMode.DARK:
            return DARK_THEME
        return LIGHT_THEME

    @property
    def is_dark(self) -> bool:
        return self._mode == ThemeMode.DARK

    def set_theme(self, mode: ThemeMode) -> None:
        """Set the current theme mode."""
        if self._mode != mode:
            self._mode = mode
            self._notify_changed()

    def toggle_theme(self) -> ThemeMode:
        """Toggle between light and dark mode."""
        if self._mode == ThemeMode.DARK:
            self.set_theme(ThemeMode.LIGHT)
        else:
            self.set_theme(ThemeMode.DARK)
        return self._mode

    def add_listener(self, callback: Callable[[], None]) -> None:
        """Add a listener for theme changes."""
        if callback not in self._on_theme_changed:
            self._on_theme_changed.append(callback)

    def remove_listener(self, callback: Callable[[], None]) -> None:
        """Remove a theme change listener."""
        if callback in self._on_theme_changed:
            self._on_theme_changed.remove(callback)

    def get_stylesheet(self) -> str:
        """Generate Qt stylesheet for current theme."""
        c = self.colors
        return f"""
/* Base Application */
QMainWindow, QDialog, QWidget {{
    background-color: {c.background};
    color: {c.text_primary};
}}

/* Menu Bar */
QMenuBar {{
    background-color: {c.foreground};
    color: {c.text_primary};
    border-bottom: 1px solid {c.border};
}}
QMenuBar::item {{
    padding: 4px 8px;
}}
QMenuBar::item:selected {{
    background-color: {c.surface};
}}
QMenu {{
    background-color: {c.foreground};
    color: {c.text_primary};
    border: 1px solid {c.border};
}}
QMenu::item:selected {{
    background-color: {c.selection_bg};
    color: {c.selection_fg};
}}
QMenu::separator {{
    height: 1px;
    background-color: {c.border};
    margin: 4px 8px;
}}

/* Tool Bar */
QToolBar {{
    background-color: {c.foreground};
    border: none;
    spacing: 2px;
    padding: 2px;
}}
QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px;
}}
QToolButton:hover {{
    background-color: {c.surface};
    border-color: {c.border};
}}
QToolButton:pressed, QToolButton:checked {{
    background-color: {c.primary};
    color: {c.selection_fg};
}}

/* Dock Widgets */
QDockWidget {{
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}
QDockWidget::title {{
    background-color: {c.surface};
    padding: 6px;
    border-bottom: 1px solid {c.border};
}}

/* Scroll Bars */
QScrollBar:vertical {{
    background-color: {c.background};
    width: 12px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background-color: {c.secondary};
    border-radius: 6px;
    min-height: 20px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {c.primary};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
}}
QScrollBar:horizontal {{
    background-color: {c.background};
    height: 12px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background-color: {c.secondary};
    border-radius: 6px;
    min-width: 20px;
    margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {c.primary};
}}

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {c.input_bg};
    color: {c.text_primary};
    border: 1px solid {c.input_border};
    border-radius: 4px;
    padding: 4px 8px;
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {c.input_focus};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {c.foreground};
    color: {c.text_primary};
    selection-background-color: {c.selection_bg};
    border: 1px solid {c.border};
}}

/* Buttons */
QPushButton {{
    background-color: {c.primary};
    color: {c.selection_fg};
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {c.primary_hover};
}}
QPushButton:pressed {{
    background-color: {c.primary};
}}
QPushButton:disabled {{
    background-color: {c.surface};
    color: {c.text_disabled};
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {c.border};
    background-color: {c.foreground};
}}
QTabBar::tab {{
    background-color: {c.surface};
    color: {c.text_secondary};
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {c.foreground};
    color: {c.text_primary};
}}
QTabBar::tab:hover:!selected {{
    background-color: {c.border};
}}

/* Tables */
QTableWidget, QTableView, QTreeWidget, QTreeView, QListWidget, QListView {{
    background-color: {c.foreground};
    color: {c.text_primary};
    border: 1px solid {c.border};
    gridline-color: {c.border};
}}
QHeaderView::section {{
    background-color: {c.surface};
    color: {c.text_primary};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {c.border};
    border-right: 1px solid {c.border};
}}
QTableWidget::item:selected, QTreeWidget::item:selected, QListWidget::item:selected {{
    background-color: {c.selection_bg};
    color: {c.selection_fg};
}}

/* Group Box */
QGroupBox {{
    font-weight: bold;
    border: 1px solid {c.border};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 12px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}}

/* Progress Bar */
QProgressBar {{
    background-color: {c.surface};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {c.primary};
    border-radius: 4px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {c.foreground};
    border-top: 1px solid {c.border};
}}

/* Tooltips */
QToolTip {{
    background-color: {c.foreground};
    color: {c.text_primary};
    border: 1px solid {c.border};
    padding: 4px;
}}

/* Checkbox and Radio */
QCheckBox, QRadioButton {{
    color: {c.text_primary};
    spacing: 8px;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
}}
QCheckBox::indicator:checked {{
    background-color: {c.primary};
    border-radius: 3px;
}}
QRadioButton::indicator:checked {{
    background-color: {c.primary};
    border-radius: 8px;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {c.border};
}}
QSplitter::handle:hover {{
    background-color: {c.primary};
}}
"""

    def _notify_changed(self) -> None:
        """Notify all listeners of theme change."""
        for callback in self._on_theme_changed:
            with contextlib.suppress(Exception):
                callback()


# Singleton instance
_theme_manager: ThemeManager | None = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
