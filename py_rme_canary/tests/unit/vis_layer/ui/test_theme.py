"""Unit tests for theme system."""

from __future__ import annotations

import pytest


class TestColors:
    """Tests for color tokens."""

    def test_base_colors_defined(self):
        """Test base colors are defined."""
        from py_rme_canary.vis_layer.ui.theme.colors import BASE

        assert "bg_primary" in BASE
        assert "bg_secondary" in BASE
        assert "accent" in BASE

    def test_color_format(self):
        """Test colors are valid hex format."""
        from py_rme_canary.vis_layer.ui.theme.colors import BASE

        for name, color in BASE.items():
            assert color.startswith("#"), f"{name} should start with #"
            # Should be 7 chars (#RRGGBB) or 9 chars (#RRGGBBAA)
            assert len(color) in (7, 9), f"{name} has invalid length"

    def test_semantic_colors_defined(self):
        """Test semantic colors are defined."""
        from py_rme_canary.vis_layer.ui.theme.colors import SEMANTIC

        assert "success" in SEMANTIC
        assert "warning" in SEMANTIC
        assert "error" in SEMANTIC


class TestStyles:
    """Tests for style generation."""

    def test_generate_stylesheet(self):
        """Test stylesheet can be generated."""
        from py_rme_canary.vis_layer.ui.theme.styles import generate_stylesheet

        stylesheet = generate_stylesheet()

        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0

    def test_stylesheet_contains_widgets(self):
        """Test stylesheet includes common widgets."""
        from py_rme_canary.vis_layer.ui.theme.styles import generate_stylesheet

        stylesheet = generate_stylesheet()

        assert "QPushButton" in stylesheet
        assert "QLineEdit" in stylesheet
        assert "QComboBox" in stylesheet

    def test_stylesheet_has_colors(self):
        """Test stylesheet uses our colors."""
        from py_rme_canary.vis_layer.ui.theme.colors import BASE
        from py_rme_canary.vis_layer.ui.theme.styles import generate_stylesheet

        stylesheet = generate_stylesheet()

        # Should contain our accent color
        assert BASE["accent"].upper() in stylesheet.upper() or BASE["accent"].lower() in stylesheet.lower()


class TestIntegration:
    """Tests for theme integration."""

    @pytest.fixture
    def app(self):
        pytest.importorskip("PyQt6")
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_apply_modern_theme(self, app):
        """Test applying modern theme."""
        from py_rme_canary.vis_layer.ui.theme.integration import apply_modern_theme

        result = apply_modern_theme(app)

        assert result is True

    def test_theme_applied_to_app(self, app):
        """Test theme is actually applied."""
        from py_rme_canary.vis_layer.ui.theme.integration import apply_modern_theme

        apply_modern_theme(app)

        stylesheet = app.styleSheet()
        assert len(stylesheet) > 0


class TestContextMenus:
    """Tests for context menu builder."""

    @pytest.fixture
    def app(self):
        pytest.importorskip("PyQt6")
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_builder_creation(self, app):
        """Test creating context menu builder."""
        from py_rme_canary.vis_layer.ui.menus.context_menus import ContextMenuBuilder

        builder = ContextMenuBuilder()
        assert builder is not None

    def test_add_action(self, app):
        """Test adding action to menu."""
        from py_rme_canary.vis_layer.ui.menus.context_menus import ContextMenuBuilder

        builder = ContextMenuBuilder()
        builder.add_action("Test Action", lambda: None)

        menu = builder.build()
        assert menu.actions()  # Should have at least one action

    def test_add_separator(self, app):
        """Test adding separator."""
        from py_rme_canary.vis_layer.ui.menus.context_menus import ContextMenuBuilder

        builder = ContextMenuBuilder()
        builder.add_action("Action 1", lambda: None)
        builder.add_separator()
        builder.add_action("Action 2", lambda: None)

        menu = builder.build()
        assert len(menu.actions()) == 3  # 2 actions + 1 separator

    def test_add_submenu(self, app):
        """Test adding submenu."""
        from py_rme_canary.vis_layer.ui.menus.context_menus import ContextMenuBuilder

        builder = ContextMenuBuilder()
        builder.add_submenu("Submenu")
        builder.add_action("Sub Action", lambda: None)
        builder.end_submenu()

        menu = builder.build()
        # Should have one item (the submenu)
        assert len(menu.actions()) >= 1

    def test_builder_chaining(self, app):
        """Test fluent builder pattern."""
        from py_rme_canary.vis_layer.ui.menus.context_menus import ContextMenuBuilder

        menu = (
            ContextMenuBuilder()
            .add_action("Copy", lambda: None)
            .add_action("Paste", lambda: None)
            .add_separator()
            .add_action("Delete", lambda: None)
            .build()
        )

        assert menu is not None
        assert len(menu.actions()) == 4

    def test_tile_context_menu(self, app):
        """Test tile context menu."""
        from py_rme_canary.vis_layer.ui.menus.context_menus import TileContextMenu

        menu = TileContextMenu()
        menu.set_callbacks(
            {
                "copy": lambda: None,
                "paste": lambda: None,
            }
        )

        assert menu is not None
