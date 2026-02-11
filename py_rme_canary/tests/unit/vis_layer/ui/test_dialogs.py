"""Unit tests for dialog components."""

from __future__ import annotations

import pytest

# Skip tests if PyQt6 not available
pytest.importorskip("PyQt6")


class TestWelcomeDialog:
    """Tests for welcome dialog."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_welcome_dialog_creation(self, app):
        """Test creating welcome dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.welcome_dialog import WelcomeDialog

        dialog = WelcomeDialog()
        assert dialog is not None
        assert dialog.windowTitle() == "Welcome"

    def test_welcome_dialog_with_recent_files(self, app):
        """Test welcome dialog with recent files."""
        from py_rme_canary.vis_layer.ui.dialogs.welcome_dialog import WelcomeDialog

        recent = [
            ("/path/to/map1.otbm", "map1.otbm"),
            ("/path/to/map2.otbm", "map2.otbm"),
        ]
        dialog = WelcomeDialog(recent_files=recent)

        # Should show recent files
        assert dialog.recent_list.count() == 2


class TestSettingsDialog:
    """Tests for settings dialog."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_settings_dialog_creation(self, app):
        """Test creating settings dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog()
        assert dialog is not None
        assert dialog.windowTitle() == "Preferences"

    def test_settings_categories(self, app):
        """Test settings has all categories."""
        from py_rme_canary.vis_layer.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog()

        # Should have 5 categories (General/Editor/Graphics/Interface/Client Version)
        assert dialog._nav_list.count() == 5

    def test_category_navigation(self, app):
        """Test navigating between categories."""
        from py_rme_canary.vis_layer.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog()

        # Select each category
        for i in range(dialog._nav_list.count()):
            dialog._nav_list.setCurrentRow(i)
            assert dialog._stack.currentIndex() == i


class TestGlobalSearchDialog:
    """Tests for global search dialog."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_search_dialog_creation(self, app):
        """Test creating search dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.global_search import GlobalSearchDialog

        dialog = GlobalSearchDialog()
        assert dialog is not None

    def test_search_type_checkboxes(self, app):
        """Test search type checkboxes."""
        from py_rme_canary.vis_layer.ui.dialogs.global_search import GlobalSearchDialog

        dialog = GlobalSearchDialog()

        # All should be checked by default
        assert dialog.check_items.isChecked()
        assert dialog.check_houses.isChecked()
        assert dialog.check_spawns.isChecked()
        assert dialog.check_waypoints.isChecked()
        assert dialog.check_zones.isChecked()


class TestNavigationDialogs:
    """Tests for navigation dialogs."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_goto_dialog_creation(self, app):
        """Test creating goto dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.navigation_dialogs import GoToPositionDialog

        dialog = GoToPositionDialog()
        assert dialog is not None

    def test_goto_dialog_with_position(self, app):
        """Test goto dialog with initial position."""
        from py_rme_canary.vis_layer.ui.dialogs.navigation_dialogs import GoToPositionDialog

        dialog = GoToPositionDialog(current_x=100, current_y=200, current_z=7)

        assert dialog.x_spin.value() == 100
        assert dialog.y_spin.value() == 200
        assert dialog.z_spin.value() == 7

    def test_find_dialog_creation(self, app):
        """Test creating find dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.navigation_dialogs import FindItemDialog

        dialog = FindItemDialog()
        assert dialog is not None


class TestWaypointDialog:
    """Tests for waypoint dialog."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_waypoint_dialog_creation(self, app):
        """Test creating waypoint dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.waypoint_dialog import WaypointListDialog

        dialog = WaypointListDialog()
        assert dialog is not None

    def test_quick_add_creation(self, app):
        """Test creating quick add dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.waypoint_dialog import WaypointQuickAdd

        dialog = WaypointQuickAdd(position=(100, 200, 7))
        assert dialog is not None

    def test_quick_add_get_name(self, app):
        """Test getting name from quick add."""
        from py_rme_canary.vis_layer.ui.dialogs.waypoint_dialog import WaypointQuickAdd

        dialog = WaypointQuickAdd(position=(100, 200, 7))
        dialog.name_input.setText("Test Waypoint")

        assert dialog.get_name() == "Test Waypoint"


class TestHouseDialog:
    """Tests for house dialog."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_house_dialog_creation(self, app):
        """Test creating house dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.house_dialog import HouseListDialog

        dialog = HouseListDialog()
        assert dialog is not None

    def test_house_edit_dialog(self, app):
        """Test house edit dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.house_dialog import HouseEditDialog

        dialog = HouseEditDialog(house_id=1, house_name="Test House")

        assert dialog.name_input.text() == "Test House"


class TestSpawnManagerDialog:
    """Tests for spawn manager dialog."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_spawn_manager_creation(self, app):
        """Test creating spawn manager dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.spawn_manager import SpawnManagerDialog

        dialog = SpawnManagerDialog()
        assert dialog is not None

    def test_spawn_manager_tabs(self, app):
        """Test spawn manager has two tabs."""
        from py_rme_canary.vis_layer.ui.dialogs.spawn_manager import SpawnManagerDialog

        dialog = SpawnManagerDialog()

        # Should have monster and NPC tabs
        assert dialog.tabs.count() == 2


class TestFindReplaceDialog:
    """Tests for find/replace dialog."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_find_replace_creation(self, app):
        """Test creating find/replace dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.find_replace_dialog import ItemFindReplaceDialog

        dialog = ItemFindReplaceDialog()
        assert dialog is not None

    def test_delete_mode_toggle(self, app):
        """Test delete mode toggle."""

        from py_rme_canary.vis_layer.ui.dialogs.find_replace_dialog import ItemFindReplaceDialog

        dialog = ItemFindReplaceDialog()

        # Initially replace mode
        assert dialog.replace_id.isEnabled()

        # Toggle delete mode
        dialog.delete_mode.setChecked(True)

        # Replace ID should be disabled
        assert not dialog.replace_id.isEnabled()


class TestShortcutsDialog:
    """Tests for keyboard shortcuts dialog."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_shortcuts_dialog_creation(self, app):
        """Test creating shortcuts dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.shortcuts_dialog import KeyboardShortcutsDialog

        dialog = KeyboardShortcutsDialog()
        assert dialog is not None

    def test_shortcuts_search(self, app):
        """Test searching shortcuts."""
        from py_rme_canary.vis_layer.ui.dialogs.shortcuts_dialog import KeyboardShortcutsDialog

        dialog = KeyboardShortcutsDialog()

        # Search for "undo"
        dialog.search_input.setText("undo")
        dialog._on_search("undo")

        # Some categories should be filtered
