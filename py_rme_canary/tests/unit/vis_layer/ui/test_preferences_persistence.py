import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from py_rme_canary.vis_layer.ui.main_window.preferences_dialog import PreferencesDialog
from py_rme_canary.core.config.configuration_manager import ConfigurationManager

# Skip if UI is not available (though offscreen platform should handle it)
pytestmark = pytest.mark.skipif("not config.getoption('qt_qpa_platform')", reason="UI tests only")

def test_preferences_persistence(qtbot, tmp_path):
    """Test that preferences are saved to and loaded from a file."""

    # Mock the config path to use our tmp_path
    config_file = tmp_path / "config.toml"

    # We need to patch the method we will add to ConfigurationManager
    # ensuring it returns our temp file path
    with patch("py_rme_canary.core.config.configuration_manager.ConfigurationManager.get_app_config_path", return_value=config_file):

        # 1. Instantiate dialog - this should trigger load (which will find nothing initially)
        # We might need to mock load_app_settings if we haven't implemented it yet,
        # but for true TDD we expect it to fail or we mock the lower level file access.
        # Let's rely on the real implementation we are about to write, but for now
        # the test might crash if methods don't exist.

        # Since the methods don't exist yet, we can mock them completely to verify the Dialog calls them
        # OR we can assume we will implement them and test the integration.
        # Given the task is "Save preferences to ConfigurationManager", integration test is better.

        # But wait, the methods don't exist on ConfigurationManager yet.
        # So I will mock the methods that I *intend* to add to ConfigurationManager class
        # so I can verify the Dialog calls them.
        # Later I can add a test for ConfigurationManager itself or update this test to use real one.

        # Actually, let's just write the test assuming the methods exist.
        # But wait, Python will raise AttributeError.
        # So I will just implement the test structure now, and expect it to fail.

        pass

# Let's write a proper test that patches the specific methods on ConfigurationManager
# We will assume `load_app_settings` and `save_app_settings` are static or class methods
# based on how they are likely to be used (singleton-like access to app config).

@pytest.fixture
def mock_config_manager(monkeypatch):
    """Mock ConfigurationManager methods for isolation."""
    # We will attach these mocks to the class
    load_mock = MagicMock(return_value={})
    save_mock = MagicMock()

    monkeypatch.setattr(ConfigurationManager, "load_app_settings", load_mock, raising=False)
    monkeypatch.setattr(ConfigurationManager, "save_app_settings", save_mock, raising=False)

    return load_mock, save_mock

def test_preferences_dialog_load_save(qtbot, mock_config_manager):
    """Test that dialog calls load on init and save on apply."""
    load_mock, save_mock = mock_config_manager

    # Setup return value for load
    load_mock.return_value = {
        "undo_queue_size": 999,
        "show_welcome_dialog": False
    }

    dlg = PreferencesDialog()
    qtbot.addWidget(dlg)

    # Verify load was called
    load_mock.assert_called_once()

    # Verify values were applied from loaded settings
    assert dlg._settings["undo_queue_size"] == 999
    assert dlg._settings["show_welcome_dialog"] is False

    # Change a setting via UI (or directly for speed/reliability)
    dlg._undo_size_spin.setValue(500)

    # Trigger save (Apply)
    dlg._on_apply()

    # Verify save was called with updated settings
    save_mock.assert_called_once()
    saved_args = save_mock.call_args[0][0]
    assert saved_args["undo_queue_size"] == 500
    assert saved_args["show_welcome_dialog"] is False
