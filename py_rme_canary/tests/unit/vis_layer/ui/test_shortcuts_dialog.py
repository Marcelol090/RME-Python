"""Tests for keyboard shortcuts dialog."""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")


@pytest.fixture
def app():
    from PyQt6.QtWidgets import QApplication

    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


def test_shortcuts_dialog_init(app):
    from py_rme_canary.vis_layer.ui.dialogs.shortcuts_dialog import KeyboardShortcutsDialog

    dialog = KeyboardShortcutsDialog()
    assert dialog.windowTitle() == "Keyboard Shortcuts"
    # Verify it has categories
    assert len(dialog._categories) > 0
