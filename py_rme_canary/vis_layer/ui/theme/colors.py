"""Theme color tokens and QColor helpers."""

from __future__ import annotations

from PyQt6.QtGui import QColor

from py_rme_canary.vis_layer.ui.theme import get_theme_manager

# Backward-compatible exports consumed by legacy tests/modules.
BASE: dict[str, str] = {
    "bg_primary": "#1E1E2E",
    "bg_secondary": "#2A2A3E",
    "surface": "#363650",
    "text_primary": "#E5E5E7",
    "text_secondary": "#A1A1AA",
    "accent": "#7C3AED",
    "border": "#404060",
}

SEMANTIC: dict[str, str] = {
    "success": "#3EEA8D",
    "warning": "#FFB84D",
    "error": "#FF647F",
    "info": "#7BE7FF",
}


def _resolve_theme_color(name: str) -> str:
    tm = get_theme_manager()
    color = tm.tokens["color"]
    aliases: dict[str, str] = {
        "primary": color["brand"]["primary"],
        "secondary": color["brand"]["secondary"],
        "background": color["surface"]["primary"],
        "surface": color["surface"]["secondary"],
        "surface_variant": color["surface"]["tertiary"],
        "text_primary": color["text"]["primary"],
        "text_secondary": color["text"]["secondary"],
        "text_disabled": color["text"]["disabled"],
        "border": color["border"]["default"],
        "error": color["state"]["error"],
    }
    if name in BASE:
        return BASE[name]
    if name in SEMANTIC:
        return SEMANTIC[name]
    return aliases.get(name, color["brand"]["primary"])


def get_qcolor(hex_color: str, alpha: int = 255) -> QColor:
    """Convert hex string to QColor with optional alpha.

    Args:
        hex_color: Hex color string (e.g., "#FF0000")
        alpha: Alpha channel (0-255)

    Returns:
        QColor object
    """
    c = QColor(hex_color)
    c.setAlpha(alpha)
    return c


def get_theme_color(name: str, alpha: int = 255) -> QColor:
    """Get a theme color by name as QColor.

    Args:
        name: Name of the color property in ThemeColors (e.g., 'primary', 'background')
        alpha: Alpha channel (0-255)

    Returns:
        QColor object
    """
    color_str = _resolve_theme_color(name)
    # Handle rgba strings if present (though ModernTheme mostly uses hex)
    if color_str.startswith("rgba"):
        # Parser for rgba(r, g, b, a) or rgba(r, g, b, a_float)
        try:
            parts = color_str.replace("rgba(", "").replace(")", "").split(",")
            r = int(parts[0].strip())
            g = int(parts[1].strip())
            b = int(parts[2].strip())
            a_val = parts[3].strip()
            # Handle float alpha (0.0-1.0) or int alpha (0-255)
            a = int(float(a_val) * 255) if "." in a_val else int(a_val)
            return QColor(r, g, b, a)
        except (ValueError, IndexError, AttributeError):
            # Fallback
            return QColor(color_str)

    return get_qcolor(color_str, alpha)
