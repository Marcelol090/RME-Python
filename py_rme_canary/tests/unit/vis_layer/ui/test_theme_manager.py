"""Tests for ThemeManager and stylesheet generation."""

from __future__ import annotations

import pytest

try:
    from py_rme_canary.vis_layer.ui.theme import THEME_TOKENS, get_theme_manager
except ImportError:
    pytest.skip("PyQt6 not installed", allow_module_level=True)


def test_theme_manager_singleton() -> None:
    tm1 = get_theme_manager()
    tm2 = get_theme_manager()
    assert tm1 is tm2


def test_theme_registration() -> None:
    # Verify required Noct themes are present
    assert "glass_morphism" in THEME_TOKENS
    assert "glass_8bit" in THEME_TOKENS
    assert "liquid_glass" in THEME_TOKENS


def test_glass_morphism_theme_colors() -> None:
    theme = THEME_TOKENS["glass_morphism"]
    colors = theme["color"]
    assert colors["brand"]["primary"].lower() == "#3eea8d"
    assert "rgba(" in colors["surface"]["primary"].lower()


def test_theme_switching() -> None:
    tm = get_theme_manager()
    tm.set_theme("glass_8bit")
    assert tm.current_theme == "glass_8bit"

    stylesheet = tm._generate_stylesheet(tm.tokens)
    assert "QWidget" in stylesheet

    with pytest.raises(ValueError):
        tm.set_theme("non_existent")


def test_loading_dialog_style_components() -> None:
    tm = get_theme_manager()
    tm.set_theme("glass_morphism")
    stylesheet = tm._generate_stylesheet(tm.tokens)

    assert "QProgressBar" in stylesheet
    assert "QProgressBar::chunk" in stylesheet
