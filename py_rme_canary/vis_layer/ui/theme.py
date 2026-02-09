"""
Theme Manager with Design Tokens for Canary Studio Map Editor.
Based on ui_instructions.md - PyQt6 UI/UX Development Instructions.
"""

from __future__ import annotations

from typing import TypedDict, Dict

from PyQt6.QtWidgets import QApplication


class ThemeColors(TypedDict):
    """Color tokens structure."""
    brand: Dict[str, str]
    surface: Dict[str, str]
    text: Dict[str, str]
    border: Dict[str, str]
    state: Dict[str, str]

class ThemeTokens(TypedDict):
    """Type definition for theme tokens."""
    color: ThemeColors
    spacing: Dict[str, int]
    radius: Dict[str, int]


# Design Tokens - Premium Dark Theme (Dracula Inspired)
DARK_THEME: ThemeTokens = {
    "color": {
        "brand": {
            "primary": "#BD93F9",
            "secondary": "#FF79C6",
            "active": "#50FA7B",
        },
        "surface": {
            "primary": "#282A36",
            "secondary": "#44475A",
            "tertiary": "#6272A4",
            "elevated": "#44475A",
            "overlay": "rgba(40, 42, 54, 0.8)",
        },
        "text": {
            "primary": "#F8F8F2",
            "secondary": "#BD93F9",
            "tertiary": "#6272A4",
            "disabled": "#6272A4",
        },
        "border": {
            "default": "#6272A4",
            "strong": "#BD93F9",
            "interactive": "#FF79C6",
        },
        "state": {
            "hover": "#FF79C6",
            "active": "#50FA7B",
            "error": "#FF5555",
        }
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
    }
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
        }
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
    }
}

# Theme registry
THEME_TOKENS: dict[str, ThemeTokens] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
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

/* ==================== Menus (Elevated) ==================== */
QMenuBar {{
    background-color: {c["surface"]["primary"]};
    border-bottom: 1px solid {c["surface"]["secondary"]};
}}

QMenuBar::item {{
    padding: 8px 12px;
    background: transparent;
}}

QMenuBar::item:selected {{
    background: rgba(255, 255, 255, 0.1);
    border-radius: {r["sm"]}px;
}}

QMenu {{
    background-color: {c["surface"]["elevated"]};
    border: 1px solid {c["border"]["default"]};
    border-radius: {r["md"]}px;
    padding: {s["xs"]}px;
}}

QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: {r["sm"]}px;
    margin: 2px;
}}

QMenu::item:selected {{
    background-color: {c["brand"]["primary"]};
    color: {c["text"]["primary"]};
}}

QMenu::separator {{
    height: 1px;
    background: {c["border"]["default"]};
    margin: 4px;
}}

/* ==================== Dock Widgets (Clean) ==================== */
QDockWidget {{
    titlebar-close-icon: url(:/icons/close.svg);
    titlebar-normal-icon: url(:/icons/float.svg);
}}

QDockWidget::title {{
    background-color: {c["surface"]["primary"]};
    padding: 8px;
    border-bottom: 1px solid {c["surface"]["secondary"]};
    font-weight: 600;
    color: {c["text"]["secondary"]};
}}

/* ==================== Tab Widgets (Modern) ==================== */
QTabWidget::pane {{
    background-color: {c["surface"]["primary"]};
    border: 1px solid {c["surface"]["secondary"]};
    border-radius: {r["md"]}px;
    top: -1px; /* Overlap header border */
}}

QTabBar::tab {{
    background-color: {c["surface"]["primary"]};
    color: {c["text"]["tertiary"]};
    padding: 8px 16px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
    margin-right: 4px;
}}

QTabBar::tab:selected {{
    color: {c["text"]["primary"]};
    border-bottom: 2px solid {c["brand"]["primary"]};
}}

QTabBar::tab:hover:!selected {{
    background-color: rgba(255, 255, 255, 0.05);
    color: {c["text"]["secondary"]};
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

/* ==================== Process Bar ==================== */
QProgressBar {{
    border: none;
    background-color: {c["surface"]["secondary"]};
    border-radius: {r["sm"]}px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {c["brand"]["primary"]};
    border-radius: {r["sm"]}px;
}}
"""


# Singleton accessor
def get_theme_manager() -> ThemeManager:
    """Get the singleton ThemeManager instance."""
    return ThemeManager()
