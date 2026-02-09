"""
Tests for ModernDialog.
"""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout

from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog


def test_modern_dialog_structure(qtbot):
    """Test ModernDialog basic structure."""
    dialog = ModernDialog(title="Test Dialog")
    qtbot.addWidget(dialog)
    dialog.show()

    # Check title
    assert dialog.title_label.text() == "Test Dialog"

    # Check flags
    assert dialog.windowFlags() & Qt.WindowType.FramelessWindowHint

    # Check content area exists
    assert dialog.content_area is not None
    assert dialog.content_layout is not None


def test_modern_dialog_content(qtbot):
    """Test adding content to ModernDialog."""
    dialog = ModernDialog()
    qtbot.addWidget(dialog)
    dialog.show()

    # Add content
    layout = dialog.content_layout
    label = QLabel("Hello World")
    layout.addWidget(label)
    label.show() # Explicitly show

    assert label.isVisibleTo(dialog)


def test_modern_dialog_footer(qtbot):
    """Test adding buttons to footer."""
    dialog = ModernDialog()
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)

    # Initially hidden
    # Note: isVisible() checks if widget AND parents are visible.
    # footer parent is dialog.
    # dialog is visible.
    # footer setVisible(False) in constructor.
    assert not dialog.footer.isVisible()

    # Add button
    btn = dialog.add_button("OK", role="primary")

    # Now visible
    assert dialog.footer.isVisible()
    assert btn.text() == "OK"

    # Click button
    with qtbot.waitSignal(btn.clicked):
        qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)


def test_modern_dialog_close(qtbot):
    """Test close button calls reject."""
    dialog = ModernDialog()
    qtbot.addWidget(dialog)
    dialog.show()

    # Mock reject
    rejected = False
    def on_reject():
        nonlocal rejected
        rejected = True

    dialog.rejected.connect(on_reject)

    # Click close button
    qtbot.mouseClick(dialog.close_btn, Qt.MouseButton.LeftButton)

    assert rejected
