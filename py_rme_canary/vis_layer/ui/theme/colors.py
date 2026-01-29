"""Theme color tokens for tests and integration."""
from __future__ import annotations

from py_rme_canary.vis_layer.ui.theme.modern_theme import ModernTheme

BASE = {
    "bg_primary": ModernTheme.colors.background,
    "bg_secondary": ModernTheme.colors.surface,
    "accent": ModernTheme.colors.primary,
    "text_primary": ModernTheme.colors.text_primary,
    "text_secondary": ModernTheme.colors.text_secondary,
    "border": ModernTheme.colors.border,
}

SEMANTIC = {
    "success": ModernTheme.colors.success,
    "warning": ModernTheme.colors.warning,
    "error": ModernTheme.colors.error,
    "info": ModernTheme.colors.info,
}
