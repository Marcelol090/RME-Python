"""
Theme Manager with Design Tokens for Canary Studio Map Editor.
Based on ui_instructions.md - PyQt6 UI/UX Development Instructions.
"""

from __future__ import annotations

import contextlib
from typing import TypedDict

from PyQt6.QtWidgets import QApplication, QWidget


class ThemeColors(TypedDict):
    """Color tokens structure."""

    brand: dict[str, str]
    surface: dict[str, str]
    text: dict[str, str]
    border: dict[str, str]
    state: dict[str, str]


class ThemeTokens(TypedDict):
    """Type definition for theme tokens."""

    color: ThemeColors
    spacing: dict[str, int]
    radius: dict[str, int]


# Design Tokens - Antigravity Theme (Deep Glassmorphism)
DARK_THEME: ThemeTokens = {
    "color": {
        "brand": {
            "primary": "#7C3AED",  # Violet 600
            "secondary": "#8B5CF6",  # Violet 500
            "active": "#A78BFA",  # Violet 400
        },
        "surface": {
            "primary": "rgba(16, 16, 24, 0.85)",  # Deep glass
            "secondary": "rgba(19, 19, 29, 0.6)",  # Panel glass
            "tertiary": "rgba(255, 255, 255, 0.04)",  # Subtle interactive
            "elevated": "rgba(23, 23, 35, 0.95)",  # Popups/Menus
            "overlay": "rgba(0, 0, 0, 0.7)",  # Modal backdrop
        },
        "text": {
            "primary": "#E5E5E7",  # Zinc 200
            "secondary": "rgba(161, 161, 170, 0.8)",  # Zinc 400
            "tertiary": "rgba(113, 113, 122, 0.6)",  # Zinc 500
            "disabled": "rgba(82, 82, 91, 0.5)",  # Zinc 600
        },
        "border": {
            "default": "rgba(255, 255, 255, 0.06)",  # Glass edge
            "strong": "rgba(255, 255, 255, 0.1)",  # Focus edge
            "interactive": "rgba(139, 92, 246, 0.4)",  # Violet edge
        },
        "state": {
            "hover": "rgba(139, 92, 246, 0.12)",
            "active": "rgba(139, 92, 246, 0.25)",
            "error": "#EF4444",  # Red 500
        },
    },
    "spacing": {
        "xs": 4,
        "sm": 8,
        "md": 16,
        "lg": 24,
        "xl": 32,
        "xxl": 48,
    },
    "radius": {
        "sm": 6,
        "md": 10,
        "lg": 16,
        "xl": 24,
        "round": 9999,
    },
}

# Design Tokens - Premium Light Theme (Nord Light Inspired)
LIGHT_THEME: ThemeTokens = {
    "color": {
        "brand": {
            "primary": "#5E81AC",
            "secondary": "#81A1C1",
            "active": "#88C0D0",
        },
        "surface": {
            "primary": "#ECEFF4",
            "secondary": "#E5E9F0",
            "tertiary": "#D8DEE9",
            "elevated": "#FFFFFF",
            "overlay": "rgba(46, 52, 64, 0.3)",
        },
        "text": {
            "primary": "#2E3440",
            "secondary": "#4C566A",
            "tertiary": "#D8DEE9",
            "disabled": "#D8DEE9",
        },
        "border": {
            "default": "#D8DEE9",
            "strong": "#4C566A",
            "interactive": "#5E81AC",
        },
        "state": {
            "hover": "#81A1C1",
            "active": "#88C0D0",
            "error": "#BF616A",
        },
    },
    "spacing": {
        "xs": 4,
        "sm": 8,
        "md": 16,
        "lg": 24,
        "xl": 32,
        "xxl": 48,
    },
    "radius": {
        "sm": 4,
        "md": 8,
        "lg": 12,
        "xl": 16,
        "round": 9999,
    },
}

# Design Tokens - Neon Theme (Cyberpunk/High Contrast)
NEON_THEME: ThemeTokens = {
    "color": {
        "brand": {
            "primary": "#06B6D4",  # Cyan 500
            "secondary": "#22D3EE",  # Cyan 400
            "active": "#67E8F9",  # Cyan 300
        },
        "surface": {
            "primary": "rgba(5, 5, 5, 0.92)",  # Almost solid black
            "secondary": "rgba(20, 20, 20, 0.8)",  # Dark panels
            "tertiary": "rgba(255, 255, 255, 0.08)",
            "elevated": "#000000",
            "overlay": "rgba(0, 255, 255, 0.05)",  # Cyan tint overlay
        },
        "text": {
            "primary": "#FFFFFF",
            "secondary": "#94A3B8",
            "tertiary": "#64748B",
            "disabled": "#334155",
        },
        "border": {
            "default": "rgba(6, 182, 212, 0.3)",  # Cyan glow
            "strong": "rgba(6, 182, 212, 0.6)",
            "interactive": "#06B6D4",
        },
        "state": {
            "hover": "rgba(6, 182, 212, 0.15)",
            "active": "rgba(6, 182, 212, 0.3)",
            "error": "#FF0055",  # Neon Red
        },
    },
    "spacing": {
        "xs": 4,
        "sm": 8,
        "md": 16,
        "lg": 24,
        "xl": 32,
        "xxl": 48,
    },
    "radius": {
        "sm": 2,  # Sharper corners for cyberpunk
        "md": 4,
        "lg": 8,
        "xl": 12,
        "round": 9999,
    },
}

# Theme registry
THEME_TOKENS: dict[str, ThemeTokens] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
    "neon": NEON_THEME,
}


class ThemeManager:
    """
    Manages theme switching and applies stylesheets.
    """

    _instance: ThemeManager | None = None
    _current_theme: str = "dark"

    def __new__(cls) -> ThemeManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def current_theme(self) -> str:
        """Return current theme name."""
        return self._current_theme

    @property
    def tokens(self) -> ThemeTokens:
        """Return current theme tokens."""
        return THEME_TOKENS[self._current_theme]

    def toggle_theme(self) -> None:
        """Toggle between dark and light themes."""
        self._current_theme = "light" if self._current_theme == "dark" else "dark"
        self.apply_theme()

    def set_theme(self, theme_name: str) -> None:
        """Set a specific theme by name."""
        if theme_name not in THEME_TOKENS:
            raise ValueError(f"Unknown theme: {theme_name}. Available: {list(THEME_TOKENS.keys())}")
        self._current_theme = theme_name
        self.apply_theme()

    def apply_theme(self) -> None:
        """Apply the current theme to the application."""
        app = QApplication.instance()
        if app is None:
            return

        tokens = self.tokens
        qss = self._generate_stylesheet(tokens)
        app.setStyleSheet(qss)
        self._refresh_theme_aware_widgets(app)

    def _refresh_theme_aware_widgets(self, app: QApplication) -> None:
        """Call refresh hook on widgets that provide `refresh_theme()`."""
        seen: set[int] = set()
        for top in app.topLevelWidgets():
            for widget in [top, *top.findChildren(QWidget)]:
                wid = id(widget)
                if wid in seen:
                    continue
                seen.add(wid)
                refresh = getattr(widget, "refresh_theme", None)
                if callable(refresh):
                    with contextlib.suppress(Exception):
                        refresh()

    def _generate_stylesheet(self, tokens: ThemeTokens) -> str:
        """Generate QSS stylesheet from tokens with Premium Polish."""
        c = tokens["color"]
        s = tokens["spacing"]
        r = tokens["radius"]

        return f"""
/* ==================== Global ==================== */
QWidget {{
    background-color: {c["surface"]["primary"]};
    color: {c["text"]["primary"]};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
    selection-background-color: {c["state"]["active"]};
    selection-color: {c["surface"]["primary"]};
    outline: none;
}}

/* ==================== Buttons (Premium) ==================== */
QPushButton {{
    background-color: {c["surface"]["secondary"]};
    color: {c["text"]["primary"]};
    border: 1px solid {c["border"]["default"]};
    border-radius: {r["md"]}px;
    padding: {s["sm"]}px {s["md"]}px;
    min-height: 32px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {c["state"]["hover"]};
    color: {c["surface"]["primary"]}; /* High contrast on hover */
    border-color: {c["state"]["hover"]};
}}

QPushButton:pressed {{
    background-color: {c["state"]["active"]};
    border-color: {c["state"]["active"]};
    color: {c["surface"]["primary"]};
}}

QPushButton:checked {{
    background-color: {c["brand"]["primary"]};
    border-color: {c["brand"]["primary"]};
    color: {c["text"]["primary"]};
}}

QPushButton:disabled {{
    background-color: {c["surface"]["primary"]};
    border-color: {c["surface"]["secondary"]};
    color: {c["text"]["disabled"]};
}}

/* ==================== Tool Buttons (Glassmorphism) ==================== */
QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: {r["md"]}px;
    padding: 6px;
}}

QToolButton:hover {{
    background-color: rgba(255, 255, 255, 0.1);
    border-color: {c["border"]["default"]};
}}

QToolButton:checked {{
    background-color: {c["brand"]["primary"]};
    border: 1px solid {c["brand"]["primary"]};
    color: white;
}}

QToolButton:pressed {{
    background-color: {c["state"]["active"]};
}}

/* ==================== Input Fields (Modern) ==================== */
QLineEdit, QSpinBox, QComboBox {{
    background-color: {c["surface"]["secondary"]};
    color: {c["text"]["primary"]};
    border: 1px solid {c["surface"]["tertiary"]};
    border-radius: {r["md"]}px;
    padding: {s["sm"]}px;
    min-height: 32px;
    selection-background-color: {c["brand"]["primary"]};
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {c["brand"]["primary"]};
    background-color: {c["surface"]["elevated"]};
}}

QLineEdit:hover {{
    border-color: {c["text"]["secondary"]};
}}

/* ==================== Scroll Bars (Sleek) ==================== */
QScrollBar:vertical {{
    background: {c["surface"]["primary"]};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {c["surface"]["tertiary"]};
    border-radius: 5px;
    min-height: 30px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background: {c["brand"]["primary"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ==================== Tooltips (Premium) ==================== */
QToolTip {{
    background-color: {c["surface"]["elevated"]};
    color: {c["text"]["primary"]};
    border: 1px solid {c["border"]["strong"]};
    border-radius: {r["sm"]}px;
    padding: {s["xs"]}px {s["sm"]}px;
    font-weight: 500;
}}

/* ==================== Menus (Elevated Glass) ==================== */
QMenuBar {{
    background-color: {c["surface"]["primary"]};
    border-bottom: 1px solid {c["surface"]["secondary"]};
    spacing: 2px;
}}

QMenuBar::item {{
    padding: 8px 14px;
    background: transparent;
    border-radius: {r["sm"]}px;
}}

QMenuBar::item:selected {{
    background: rgba(255, 255, 255, 0.1);
    border-radius: {r["sm"]}px;
}}

QMenuBar::item:pressed {{
    background: {c["brand"]["primary"]};
    color: {c["text"]["primary"]};
}}

QMenu {{
    background-color: {c["surface"]["elevated"]};
    border: 1px solid {c["border"]["default"]};
    border-radius: {r["md"]}px;
    padding: {s["xs"]}px;
}}

QMenu::item {{
    padding: 8px 28px 8px 14px;
    border-radius: {r["sm"]}px;
    margin: 2px 4px;
    font-weight: 500;
}}

QMenu::item:selected {{
    background-color: {c["brand"]["primary"]};
    color: {c["text"]["primary"]};
}}

QMenu::item:disabled {{
    color: {c["text"]["disabled"]};
}}

QMenu::separator {{
    height: 1px;
    background: {c["border"]["default"]};
    margin: 4px 8px;
}}

QMenu::icon {{
    padding-left: 8px;
}}

/* ==================== Dock Widgets (Glass Title) ==================== */
QDockWidget {{
    titlebar-close-icon: url(:/icons/close.svg);
    titlebar-normal-icon: url(:/icons/float.svg);
    font-weight: 700;
    color: {c["text"]["secondary"]};
}}

QDockWidget::title {{
    background-color: {c["surface"]["secondary"]};
    padding: 10px 12px;
    border-bottom: 1px solid {c["border"]["default"]};
    font-weight: 700;
    color: {c["text"]["secondary"]};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent;
    border: none;
    padding: 4px;
    border-radius: {r["sm"]}px;
}}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
    background: rgba(255, 255, 255, 0.1);
}}

/* ==================== Splitter Handle ==================== */
QSplitter::handle {{
    background: {c["border"]["default"]};
    height: 3px;
    margin: 2px 24px;
    border-radius: 1px;
}}

QSplitter::handle:hover {{
    background: {c["brand"]["primary"]};
}}

QSplitter::handle:horizontal {{
    width: 3px;
    height: auto;
    margin: 24px 2px;
}}

/* ==================== Tab Widgets (Polished) ==================== */
QTabWidget::pane {{
    background-color: {c["surface"]["primary"]};
    border: 1px solid {c["surface"]["secondary"]};
    border-radius: {r["md"]}px;
    top: -1px;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {c["text"]["tertiary"]};
    padding: 10px 16px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    color: {c["text"]["primary"]};
    border-bottom: 2px solid {c["brand"]["primary"]};
    background-color: rgba(255, 255, 255, 0.03);
}}

QTabBar::tab:hover:!selected {{
    background-color: rgba(255, 255, 255, 0.05);
    color: {c["text"]["secondary"]};
    border-bottom: 2px solid {c["border"]["default"]};
}}

/* ==================== Checkboxes (Themed) ==================== */
QCheckBox {{
    spacing: 8px;
    color: {c["text"]["primary"]};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: {r["sm"]}px;
    border: 2px solid {c["border"]["default"]};
    background: {c["surface"]["secondary"]};
}}

QCheckBox::indicator:checked {{
    background: {c["brand"]["primary"]};
    border-color: {c["brand"]["primary"]};
}}

QCheckBox::indicator:hover {{
    border-color: {c["brand"]["secondary"]};
}}

/* ==================== ComboBox Dropdown (Polished) ==================== */
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
}}

QComboBox QAbstractItemView {{
    background-color: {c["surface"]["elevated"]};
    border: 1px solid {c["border"]["default"]};
    border-radius: {r["md"]}px;
    padding: 4px;
    selection-background-color: {c["brand"]["primary"]};
    selection-color: {c["text"]["primary"]};
    outline: none;
}}

/* ==================== Group Boxes ==================== */
QGroupBox {{
    border: 1px solid {c["border"]["default"]};
    border-radius: {r["lg"]}px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: 600;
    color: {c["text"]["secondary"]};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
}}

/* ==================== Progress Bar ==================== */
QProgressBar {{
    border: none;
    background-color: {c["surface"]["secondary"]};
    border-radius: {r["sm"]}px;
    text-align: center;
    min-height: 8px;
}}

QProgressBar::chunk {{
    background-color: {c["brand"]["primary"]};
    border-radius: {r["sm"]}px;
}}

/* ==================== Horizontal Scroll Bar ==================== */
QScrollBar:horizontal {{
    background: {c["surface"]["primary"]};
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {c["surface"]["tertiary"]};
    border-radius: 5px;
    min-width: 30px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {c["brand"]["primary"]};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ==================== Header View (Tables) ==================== */
QHeaderView::section {{
    background-color: {c["surface"]["secondary"]};
    color: {c["text"]["secondary"]};
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid {c["border"]["default"]};
    font-weight: 600;
}}

QHeaderView::section:hover {{
    background-color: {c["state"]["hover"]};
    color: {c["text"]["primary"]};
}}

/* ==================== Status Bar ==================== */
QStatusBar {{
    background-color: {c["surface"]["secondary"]};
    border-top: 1px solid {c["border"]["default"]};
    color: {c["text"]["secondary"]};
    font-size: 12px;
}}

QStatusBar::item {{
    border: none;
}}
"""


# Singleton accessor
def get_theme_manager() -> ThemeManager:
    """Get the singleton ThemeManager instance."""
    return ThemeManager()
