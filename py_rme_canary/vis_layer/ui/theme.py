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


# Design Tokens - Dark Theme (Primary)
DARK_THEME: ThemeTokens = {
    # Surfaces
    "surface_primary": "#0A0A0B",
    "surface_secondary": "#141416",
    "surface_tertiary": "#1E1F22",
    "surface_elevated": "#2B2D31",
    # Text
    "text_primary": "#FFFFFF",
    "text_secondary": "#B5B9BF",
    "text_tertiary": "#80848E",
    # Interactive
    "interactive_normal": "#5865F2",
    "interactive_hover": "#4752C4",
    "interactive_active": "#3C45A5",
    # Borders
    "border_default": "#3F4147",
    "border_strong": "#5A5D66",
    "border_interactive": "#5865F2",
    # Overlays
    "overlay_light": "rgba(255, 255, 255, 0.05)",
    "overlay_dark": "rgba(0, 0, 0, 0.5)",
}

# Design Tokens - Light Theme (Secondary)
LIGHT_THEME: ThemeTokens = {
    # Surfaces
    "surface_primary": "#FFFFFF",
    "surface_secondary": "#F5F5F5",
    "surface_tertiary": "#E8E8E8",
    "surface_elevated": "#FAFAFA",
    # Text
    "text_primary": "#1A1A1A",
    "text_secondary": "#4A4A4A",
    "text_tertiary": "#808080",
    # Interactive
    "interactive_normal": "#5865F2",
    "interactive_hover": "#4752C4",
    "interactive_active": "#3C45A5",
    # Borders
    "border_default": "#D0D0D0",
    "border_strong": "#A0A0A0",
    "border_interactive": "#5865F2",
    # Overlays
    "overlay_light": "rgba(0, 0, 0, 0.03)",
    "overlay_dark": "rgba(0, 0, 0, 0.3)",
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

    _instance: "ThemeManager | None" = None
    _current_theme: str = "dark"

    def __new__(cls) -> "ThemeManager":
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
        """Generate QSS stylesheet from tokens."""
        return f"""
/* ==================== Global ==================== */
QWidget {{
    background-color: {tokens['surface_primary']};
    color: {tokens['text_primary']};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}}

/* ==================== Buttons ==================== */
QPushButton {{
    background-color: {tokens['surface_tertiary']};
    color: {tokens['text_primary']};
    border: 1px solid {tokens['border_default']};
    border-radius: {RADIUS['md']}px;
    padding: {SPACING['sm']}px {SPACING['md']}px;
    min-height: 32px;
}}

QPushButton:hover {{
    background-color: {tokens['overlay_light']};
    border-color: {tokens['border_strong']};
}}

QPushButton:pressed {{
    background-color: {tokens['interactive_active']};
}}

QPushButton:checked {{
    background-color: {tokens['interactive_normal']};
    border-color: {tokens['border_interactive']};
}}

QPushButton:disabled {{
    background-color: {tokens['surface_secondary']};
    color: {tokens['text_tertiary']};
}}

/* ==================== Tool Buttons ==================== */
QToolButton {{
    background-color: {tokens['surface_tertiary']};
    border: 1px solid transparent;
    border-radius: {RADIUS['md']}px;
    padding: 4px;
}}

QToolButton:hover {{
    background-color: {tokens['overlay_light']};
    border-color: {tokens['border_default']};
}}

QToolButton:checked {{
    background-color: {tokens['interactive_normal']};
    border: 2px solid {tokens['interactive_normal']};
    color: white;
}}

/* ==================== Input Fields ==================== */
QLineEdit {{
    background-color: {tokens['surface_secondary']};
    color: {tokens['text_primary']};
    border: 1px solid {tokens['border_default']};
    border-radius: {RADIUS['lg']}px;
    padding: {SPACING['sm']}px {SPACING['md']}px;
    min-height: 32px;
}}

QLineEdit:focus {{
    border-color: {tokens['interactive_normal']};
}}

/* ==================== Scroll Bars ==================== */
QScrollBar:vertical {{
    background: {tokens['surface_primary']};
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {tokens['border_default']};
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background: {tokens['border_strong']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ==================== Tooltips ==================== */
QToolTip {{
    background-color: {tokens['surface_elevated']};
    color: {tokens['text_primary']};
    border: 1px solid {tokens['border_default']};
    border-radius: {RADIUS['sm']}px;
    padding: {SPACING['xs']}px {SPACING['sm']}px;
}}

/* ==================== Menus ==================== */
QMenu {{
    background-color: {tokens['surface_secondary']};
    border: 1px solid {tokens['border_default']};
    border-radius: {RADIUS['md']}px;
    padding: {SPACING['xs']}px;
}}

QMenu::item {{
    padding: {SPACING['sm']}px {SPACING['md']}px;
    border-radius: {RADIUS['sm']}px;
}}

QMenu::item:selected {{
    background-color: {tokens['interactive_normal']};
}}

/* ==================== Dock Widgets ==================== */
QDockWidget {{
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}

QDockWidget::title {{
    background-color: {tokens['surface_secondary']};
    padding: {SPACING['sm']}px;
    border-bottom: 1px solid {tokens['border_default']};
}}

/* ==================== Tab Widgets ==================== */
QTabWidget::pane {{
    background-color: {tokens['surface_primary']};
    border: 1px solid {tokens['border_default']};
    border-radius: {RADIUS['md']}px;
}}

QTabBar::tab {{
    background-color: {tokens['surface_secondary']};
    color: {tokens['text_secondary']};
    padding: {SPACING['sm']}px {SPACING['md']}px;
    border-top-left-radius: {RADIUS['md']}px;
    border-top-right-radius: {RADIUS['md']}px;
    min-width: 80px;
}}

QTabBar::tab:selected {{
    background-color: {tokens['surface_primary']};
    color: {tokens['text_primary']};
    border-bottom: 2px solid {tokens['interactive_normal']};
}}

QTabBar::tab:hover:!selected {{
    background-color: {tokens['overlay_light']};
}}
"""


# Singleton accessor
def get_theme_manager() -> ThemeManager:
    """Get the singleton ThemeManager instance."""
    return ThemeManager()
