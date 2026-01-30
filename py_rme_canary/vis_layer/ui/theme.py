"""
Theme Manager with Design Tokens for Canary Studio Map Editor.
Based on ui_instructions.md - PyQt6 UI/UX Development Instructions.
"""

from __future__ import annotations

from typing import TypedDict

from PyQt6.QtWidgets import QApplication


class ThemeTokens(TypedDict):
    """Type definition for theme color tokens."""

    # Surfaces
    surface_primary: str
    surface_secondary: str
    surface_tertiary: str
    surface_elevated: str
    # Text
    text_primary: str
    text_secondary: str
    text_tertiary: str
    # Interactive
    interactive_normal: str
    interactive_hover: str
    interactive_active: str
    # Borders
    border_default: str
    border_strong: str
    border_interactive: str
    # Overlays
    overlay_light: str
    overlay_dark: str


# Design Tokens - Premium Dark Theme (Dracula Inspired)
DARK_THEME: ThemeTokens = {
    # Surfaces
    "surface_primary": "#282A36",  # Background
    "surface_secondary": "#44475A",  # Panels/Sidebars
    "surface_tertiary": "#6272A4",  # Comments/Secondary Elements
    "surface_elevated": "#44475A",  # Dialogs/Popups (same as secondary for cohesion)
    # Text
    "text_primary": "#F8F8F2",  # Main Text
    "text_secondary": "#BD93F9",  # Headings/Important labels (Purple)
    "text_tertiary": "#6272A4",  # Comments/Disabled
    # Interactive
    "interactive_normal": "#BD93F9",  # Purple
    "interactive_hover": "#FF79C6",  # Pink
    "interactive_active": "#50FA7B",  # Green (Success/Active)
    # Borders
    "border_default": "#6272A4",  # Muted Blue/Purple
    "border_strong": "#BD93F9",  # Purple
    "border_interactive": "#FF79C6",  # Pink
    # Overlays
    "overlay_light": "rgba(255, 255, 255, 0.1)",
    "overlay_dark": "rgba(40, 42, 54, 0.8)",
}

# Design Tokens - Premium Light Theme (Nord Light Inspired)
LIGHT_THEME: ThemeTokens = {
    # Surfaces
    "surface_primary": "#ECEFF4",
    "surface_secondary": "#E5E9F0",
    "surface_tertiary": "#D8DEE9",
    "surface_elevated": "#FFFFFF",
    # Text
    "text_primary": "#2E3440",
    "text_secondary": "#4C566A",
    "text_tertiary": "#D8DEE9",
    # Interactive
    "interactive_normal": "#5E81AC",
    "interactive_hover": "#81A1C1",
    "interactive_active": "#88C0D0",
    # Borders
    "border_default": "#D8DEE9",
    "border_strong": "#4C566A",
    "border_interactive": "#5E81AC",
    # Overlays
    "overlay_light": "rgba(46, 52, 64, 0.05)",
    "overlay_dark": "rgba(46, 52, 64, 0.3)",
}

# Theme registry
THEME_TOKENS: dict[str, ThemeTokens] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
}


# Spacing Scale (in pixels)
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
    "xxl": 48,
}

# Border Radius Scale (in pixels)
RADIUS = {
    "sm": 4,
    "md": 8,
    "lg": 12,
    "xl": 16,
    "round": 9999,
}

# Fixed Sizes for Layout Consistency
SIZES = {
    "navbar_height": 56,
    "sidebar_collapsed": 64,
    "sidebar_default": 360,
    "sidebar_expanded": 480,
    "search_height": 40,
    "tool_button": 44,
    "brush_slot": 52,
    "asset_item": 48,
    "quick_action": 36,
}

# Animation Durations (in milliseconds)
ANIMATION = {
    "instant": 50,
    "fast": 150,
    "standard": 250,
    "slow": 500,
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
        return f"""
/* ==================== Global ==================== */
QWidget {{
    background-color: {tokens["surface_primary"]};
    color: {tokens["text_primary"]};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
    selection-background-color: {tokens["interactive_active"]};
    selection-color: {tokens["surface_primary"]};
    outline: none;
}}

/* ==================== Buttons (Premium) ==================== */
QPushButton {{
    background-color: {tokens["surface_secondary"]};
    color: {tokens["text_primary"]};
    border: 1px solid {tokens["border_default"]};
    border-radius: {RADIUS["md"]}px;
    padding: {SPACING["sm"]}px {SPACING["md"]}px;
    min-height: 32px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {tokens["interactive_hover"]};
    color: {tokens["surface_primary"]}; /* High contrast on hover */
    border-color: {tokens["interactive_hover"]};
}}

QPushButton:pressed {{
    background-color: {tokens["interactive_active"]};
    border-color: {tokens["interactive_active"]};
    color: {tokens["surface_primary"]};
}}

QPushButton:checked {{
    background-color: {tokens["interactive_normal"]};
    border-color: {tokens["interactive_normal"]};
    color: {tokens["text_primary"]};
}}

QPushButton:disabled {{
    background-color: {tokens["surface_primary"]};
    border-color: {tokens["surface_secondary"]};
    color: {tokens["text_tertiary"]};
}}

/* ==================== Tool Buttons (Glassmorphism) ==================== */
QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: {RADIUS["md"]}px;
    padding: 6px;
}}

QToolButton:hover {{
    background-color: {tokens["overlay_light"]};
    border-color: {tokens["border_default"]};
}}

QToolButton:checked {{
    background-color: {tokens["interactive_normal"]};
    border: 1px solid {tokens["interactive_normal"]};
    color: white;
}}

QToolButton:pressed {{
    background-color: {tokens["interactive_active"]};
}}

/* ==================== Input Fields (Modern) ==================== */
QLineEdit, QSpinBox, QComboBox {{
    background-color: {tokens["surface_secondary"]};
    color: {tokens["text_primary"]};
    border: 1px solid {tokens["surface_tertiary"]};
    border-radius: {RADIUS["md"]}px;
    padding: {SPACING["sm"]}px;
    min-height: 32px;
    selection-background-color: {tokens["interactive_normal"]};
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {tokens["interactive_normal"]};
    background-color: {tokens["surface_elevated"]};
}}

QLineEdit:hover {{
    border-color: {tokens["text_secondary"]};
}}

/* ==================== Scroll Bars (Sleek) ==================== */
QScrollBar:vertical {{
    background: {tokens["surface_primary"]};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {tokens["surface_tertiary"]};
    border-radius: 5px;
    min-height: 30px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background: {tokens["interactive_normal"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ==================== Tooltips (Premium) ==================== */
QToolTip {{
    background-color: {tokens["surface_elevated"]};
    color: {tokens["text_primary"]};
    border: 1px solid {tokens["border_strong"]};
    border-radius: {RADIUS["sm"]}px;
    padding: {SPACING["xs"]}px {SPACING["sm"]}px;
    font-weight: 500;
}}

/* ==================== Menus (Elevated) ==================== */
QMenuBar {{
    background-color: {tokens["surface_primary"]};
    border-bottom: 1px solid {tokens["surface_secondary"]};
}}

QMenuBar::item {{
    padding: 8px 12px;
    background: transparent;
}}

QMenuBar::item:selected {{
    background: {tokens["overlay_light"]};
    border-radius: {RADIUS["sm"]}px;
}}

QMenu {{
    background-color: {tokens["surface_elevated"]};
    border: 1px solid {tokens["border_default"]};
    border-radius: {RADIUS["md"]}px;
    padding: {SPACING["xs"]}px;
}}

QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: {RADIUS["sm"]}px;
    margin: 2px;
}}

QMenu::item:selected {{
    background-color: {tokens["interactive_normal"]};
    color: {tokens["text_primary"]};
}}

QMenu::separator {{
    height: 1px;
    background: {tokens["border_default"]};
    margin: 4px;
}}

/* ==================== Dock Widgets (Clean) ==================== */
QDockWidget {{
    titlebar-close-icon: url(:/icons/close.svg);
    titlebar-normal-icon: url(:/icons/float.svg);
}}

QDockWidget::title {{
    background-color: {tokens["surface_primary"]};
    padding: 8px;
    border-bottom: 1px solid {tokens["surface_secondary"]};
    font-weight: 600;
    color: {tokens["text_secondary"]};
}}

/* ==================== Tab Widgets (Modern) ==================== */
QTabWidget::pane {{
    background-color: {tokens["surface_primary"]};
    border: 1px solid {tokens["surface_secondary"]};
    border-radius: {RADIUS["md"]}px;
    top: -1px; /* Overlap header border */
}}

QTabBar::tab {{
    background-color: {tokens["surface_primary"]};
    color: {tokens["text_tertiary"]};
    padding: 8px 16px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
    margin-right: 4px;
}}

QTabBar::tab:selected {{
    color: {tokens["text_primary"]};
    border-bottom: 2px solid {tokens["interactive_normal"]};
}}

QTabBar::tab:hover:!selected {{
    background-color: {tokens["overlay_light"]};
    color: {tokens["text_secondary"]};
}}

/* ==================== Group Boxes ==================== */
QGroupBox {{
    border: 1px solid {tokens["border_default"]};
    border-radius: {RADIUS["lg"]}px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: 600;
    color: {tokens["text_secondary"]};
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
    background-color: {tokens["surface_secondary"]};
    border-radius: {RADIUS["sm"]}px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {tokens["interactive_normal"]};
    border-radius: {RADIUS["sm"]}px;
}}
"""


# Singleton accessor
def get_theme_manager() -> ThemeManager:
    """Get the singleton ThemeManager instance."""
    return ThemeManager()
