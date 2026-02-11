"""Tests for vis_layer.ui.splash module."""
from __future__ import annotations

import pytest

# Splash screen requires a QApplication instance.
# We skip these tests if PyQt6 is not available or no display.
pytestmark = pytest.mark.gui

try:
    from PyQt6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication([])
except Exception:
    pytest.skip('PyQt6 not available', allow_module_level=True)

from py_rme_canary.vis_layer.ui.splash import (
    _SPLASH_HEIGHT,
    _SPLASH_WIDTH,
    StartupSplash,
    _create_splash_pixmap,
)


class TestCreateSplashPixmap:
    """Test the programmatic splash image generation."""

    def test_pixmap_dimensions(self) -> None:
        pixmap = _create_splash_pixmap()
        assert pixmap.width() == _SPLASH_WIDTH
        assert pixmap.height() == _SPLASH_HEIGHT

    def test_pixmap_not_null(self) -> None:
        pixmap = _create_splash_pixmap()
        assert not pixmap.isNull()


class TestStartupSplash:
    """Test the StartupSplash QSplashScreen subclass."""

    def test_instantiation(self) -> None:
        splash = StartupSplash()
        assert splash is not None

    def test_set_phase_basic(self) -> None:
        splash = StartupSplash()
        # Should not raise
        splash.set_phase('Loading assets...')

    def test_set_phase_with_progress(self) -> None:
        splash = StartupSplash()
        splash.set_phase('Loading', progress=5, total=10)

    def test_format_message_no_progress(self) -> None:
        splash = StartupSplash()
        splash._phase = 'Init'
        splash._progress = 0
        splash._total = 0
        msg = splash._format_message()
        assert 'Init' in msg
        assert '%' not in msg

    def test_format_message_with_progress(self) -> None:
        splash = StartupSplash()
        splash._phase = 'Loading'
        splash._progress = 50
        splash._total = 100
        msg = splash._format_message()
        assert '50%' in msg

    def test_format_message_zero_progress(self) -> None:
        splash = StartupSplash()
        splash._phase = 'Starting'
        splash._progress = 0
        splash._total = 10
        msg = splash._format_message()
        assert '0%' in msg

    def test_format_message_full_progress(self) -> None:
        splash = StartupSplash()
        splash._phase = 'Done'
        splash._progress = 10
        splash._total = 10
        msg = splash._format_message()
        assert '100%' in msg
