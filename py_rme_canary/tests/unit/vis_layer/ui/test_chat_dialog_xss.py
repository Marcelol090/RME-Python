"""Tests for ChatDialog XSS vulnerability."""

from __future__ import annotations

import sys
import pytest
import importlib
from unittest.mock import MagicMock, patch

# Define mock classes to support inheritance and method calls
class MockableWidget:
    def __init__(self, parent=None):
        self._mocks = {}
    def __getattr__(self, name):
        if name not in self._mocks:
            self._mocks[name] = MagicMock()
        return self._mocks[name]

class QWidget(MockableWidget):
    def setStyleSheet(self, s): pass
    def setMinimumSize(self, w, h): pass
    def setAttribute(self, a): pass
    def setWindowFlags(self, f): pass
    def setWindowTitle(self, t): pass

class QDialog(QWidget):
    def exec(self): return 1

class QTextEdit(QWidget):
    def __init__(self):
        super().__init__()
        self.append = MagicMock()
    def setReadOnly(self, b): pass

class QLineEdit(QWidget):
    def setPlaceholderText(self, t): pass
    def text(self): return ""
    def clear(self): pass

class QPushButton(QWidget):
    def __init__(self, text=""):
        super().__init__()
        self.clicked = MagicMock()
        self.clicked.connect = MagicMock()

class QVBoxLayout(QWidget):
    def addWidget(self, w): pass
    def addLayout(self, l): pass
    def setContentsMargins(self, *args): pass
    def setSpacing(self, s): pass

class QHBoxLayout(QVBoxLayout): pass

class QFrame(QWidget):
    def setObjectName(self, n): pass

class QLabel(QWidget):
    def setFixedHeight(self, h): pass
    def setObjectName(self, n): pass

# Mock ModernDialog base
class ModernDialog(QDialog):
    def __init__(self, parent=None, title=""):
        super().__init__(parent)
        self.content_layout = QVBoxLayout()
        # Mock attributes usually set by ModernDialog
        self.history = QTextEdit()

# ---------------------------------------------------------
# Test Setup
# ---------------------------------------------------------

@pytest.fixture
def isolated_modules():
    """Patches sys.modules with mocked PyQt6 and base_modern for test isolation."""
    mock_qt = MagicMock()
    mock_qt.QWidget = QWidget
    mock_qt.QDialog = QDialog
    mock_qt.QTextEdit = QTextEdit
    mock_qt.QLineEdit = QLineEdit
    mock_qt.QPushButton = QPushButton
    mock_qt.QVBoxLayout = QVBoxLayout
    mock_qt.QHBoxLayout = QHBoxLayout
    mock_qt.QFrame = QFrame
    mock_qt.QLabel = QLabel
    mock_qt.Qt = MagicMock()

    mock_modern_module = MagicMock()
    mock_modern_module.ModernDialog = ModernDialog

    # We must patch all potential PyQt6 imports
    with patch.dict(sys.modules, {
        "PyQt6": mock_qt,
        "PyQt6.QtWidgets": mock_qt,
        "PyQt6.QtCore": mock_qt,
        "PyQt6.QtGui": mock_qt,
        "py_rme_canary.vis_layer.ui.dialogs.base_modern": mock_modern_module,
    }):
        yield

@patch("py_rme_canary.vis_layer.ui.dialogs.chat_dialog.get_theme_manager")
def test_chat_dialog_xss_vulnerability(mock_tm, isolated_modules):
    # Since we patched sys.modules, we must import/reload the module under test
    # inside the patched context to ensure it uses the mocks.
    # Note: If chat_dialog was already imported, we'd need to reload it.
    # But since we're patching sys.modules, importlib.import_module should pick up the mocks if not cached,
    # or reload if cached. Let's force reload just to be safe.

    # We need to import chat_dialog here because top-level import might have failed or used real PyQt
    try:
        from py_rme_canary.vis_layer.ui.dialogs import chat_dialog
        importlib.reload(chat_dialog)
    except ImportError:
        # If it fails to import initially (e.g. real PyQt missing), we try importing again which should now succeed with mocks
        import py_rme_canary.vis_layer.ui.dialogs.chat_dialog as chat_dialog

    ChatDialog = chat_dialog.ChatDialog

    # Setup theme manager mock
    mock_tm.return_value.tokens = {
        "color": {
            "surface": {"primary": "#000", "secondary": "#111"},
            "text": {"primary": "#FFF", "secondary": "#AAA", "tertiary": "#888"},
            "brand": {"primary": "#F00", "secondary": "#0F0"},
            "border": {"default": "#333"},
        },
        "radius": {"md": 10, "sm": 5},
    }

    dialog = ChatDialog(friend_name="Hacker")

    # Simulate receiving a message with XSS payload
    xss_payload = '<script>alert("XSS")</script>'
    dialog.append_message("Hacker", xss_payload, "12:00")

    # Check if payload was appended as-is (Vulnerable)
    # The history.append mock records the call
    last_call = dialog.history.append.call_args
    assert last_call is not None
    args, _ = last_call
    appended_html = args[0]

    # In a secure implementation, <script> should be escaped to &lt;script&gt;
    # We assert that the raw script tag is NOT present (meaning it was escaped)
    assert '<script>' not in appended_html
    assert '&lt;script&gt;' in appended_html
