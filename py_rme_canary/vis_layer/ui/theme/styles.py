"""Theme stylesheet helpers."""

from __future__ import annotations

from py_rme_canary.vis_layer.ui.theme.modern_theme import ModernTheme


def generate_stylesheet() -> str:
    """Generate a QSS stylesheet for the application."""
    return ModernTheme.get_stylesheet()
