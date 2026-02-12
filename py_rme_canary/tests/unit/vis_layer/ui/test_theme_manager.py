"""
Tests for ThemeManager to verify Dracula theme and style generation.
"""
import pytest
import sys

try:
    from PyQt6.QtWidgets import QApplication
    from py_rme_canary.vis_layer.ui.theme import ThemeManager, get_theme_manager, THEME_TOKENS
except ImportError:
    pytest.skip("PyQt6 not installed", allow_module_level=True)

def test_theme_manager_singleton():
    tm1 = get_theme_manager()
    tm2 = get_theme_manager()
    assert tm1 is tm2

def test_theme_registration():
    # Verify required themes are present
    assert "dark" in THEME_TOKENS
    assert "light" in THEME_TOKENS
    assert "dracula" in THEME_TOKENS
    assert "neon" in THEME_TOKENS

def test_dracula_theme_colors():
    dracula = THEME_TOKENS["dracula"]
    colors = dracula["color"]
    # Verify key Dracula colors
    assert colors["brand"]["primary"].lower() == "#bd93f9" # Purple
    assert colors["surface"]["primary"].lower() == "#282a36" # Background

def test_theme_switching(qapp):
    tm = get_theme_manager()
    tm.set_theme("dracula")
    assert tm.current_theme == "dracula"

    stylesheet = tm._generate_stylesheet(tm.tokens)
    assert "#282A36" in stylesheet or "#282a36" in stylesheet # Background color in QSS

    # Test invalid theme
    try:
        tm.set_theme("non_existent")
    except ValueError:
        pass
    else:
        assert False, "Should raise ValueError for unknown theme"

def test_loading_dialog_style(qapp):
    # Verify loading dialog style components are in stylesheet
    tm = get_theme_manager()
    tm.set_theme("dracula")
    stylesheet = tm._generate_stylesheet(tm.tokens)

    assert "QProgressBar" in stylesheet
    assert "QProgressBar::chunk" in stylesheet
