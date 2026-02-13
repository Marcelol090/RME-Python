"""Unit tests for modern dialogs."""

from __future__ import annotations

import pytest

# Skip tests if PyQt6 not available
pytest.importorskip("PyQt6")


class TestModernDialogs:
    """Tests for modern dialog components."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_about_dialog_is_modern(self, app):
        """Test AboutDialog inherits from ModernDialog."""
        from py_rme_canary.vis_layer.ui.dialogs.about import AboutDialog
        from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog

        dialog = AboutDialog()
        assert isinstance(dialog, ModernDialog)
        assert dialog.windowTitle() == "About"
        # Check if content layout is populated
        assert dialog.content_layout.count() > 0

    def test_map_properties_dialog_is_modern(self, app):
        """Test MapPropertiesDialog inherits from ModernDialog."""
        from py_rme_canary.vis_layer.ui.dialogs.map_dialogs import MapPropertiesDialog
        from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog

        dialog = MapPropertiesDialog()

        # Check inheritance
        assert isinstance(dialog, ModernDialog)

        # Check title
        assert dialog.windowTitle() == "Map Properties"

        # Check if content layout exists and has widgets (tabs)
        assert hasattr(dialog, "content_layout")
        assert dialog.content_layout.count() > 0

        # Check if footer exists (buttons)
        assert hasattr(dialog, "footer")
        assert not dialog.footer.isHidden()
