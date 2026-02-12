"""
Tests for ModernLoadingDialog.
"""

import pytest
try:
    from PyQt6.QtWidgets import QApplication
    from py_rme_canary.vis_layer.ui.dialogs.loading_dialog import ModernLoadingDialog
except ImportError:
    pytest.skip("PyQt6 not installed", allow_module_level=True)

# Use pytest-qt if available, otherwise manual check
try:
    import pytestqt
except ImportError:
    pytestqt = None

def test_loading_dialog_instantiation(qapp):
    # qapp fixture provided by pytest-qt or manual setup needed if not running via pytest-qt
    # But for unit test logic, we can just instantiate

    dialog = ModernLoadingDialog(title="Test Load", message="Testing...")
    assert dialog.windowTitle() == "Test Load"
    assert dialog.message_label.text() == "Testing..."
    # Indeterminate progress bar (min=0, max=0) returns -1 for value() in some Qt versions/styles
    assert dialog.progress.minimum() == 0
    assert dialog.progress.maximum() == 0
    assert dialog.logo_label.text() == "CANARY STUDIO"

def test_loading_dialog_updates(qapp):
    dialog = ModernLoadingDialog()

    dialog.set_message("New Status")
    assert dialog.message_label.text() == "New Status"

    dialog.set_progress(50)
    assert dialog.progress.value() == 50
    assert dialog.progress.maximum() == 100

    dialog.set_indeterminate()
    assert dialog.progress.maximum() == 0
