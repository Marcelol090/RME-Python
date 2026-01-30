"""Theme color tokens and QColor helpers."""
from __future__ import annotations

from PyQt6.QtGui import QColor
from py_rme_canary.vis_layer.ui.theme.modern_theme import ModernTheme

# Base colors map
BASE = {
    "bg_primary": ModernTheme.colors.background,
    "bg_secondary": ModernTheme.colors.surface,
    "accent": ModernTheme.colors.primary,
    "text_primary": ModernTheme.colors.text_primary,
    "text_secondary": ModernTheme.colors.text_secondary,
    "border": ModernTheme.colors.border,
}

# Semantic colors map
SEMANTIC = {
    "success": ModernTheme.colors.success,
    "warning": ModernTheme.colors.warning,
    "error": ModernTheme.colors.error,
    "info": ModernTheme.colors.info,
}

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
    color_str = getattr(ModernTheme.colors, name, "#000000")
    # Handle rgba strings if present (though ModernTheme mostly uses hex)
    if color_str.startswith("rgba"):
        # Simple parser for rgba(r, g, b, a)
        try:
            parts = color_str.replace("rgba(", "").replace(")", "").split(",")
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            a_float = float(parts[3])
            return QColor(r, g, b, int(a_float * 255))
        except:
            return QColor(color_str)
            
    return get_qcolor(color_str, alpha)
