
"""Security tests for ChatDialog UI."""

import sys
from unittest.mock import MagicMock, patch
import pytest

# Fixture to mock PyQt6 and dependencies
@pytest.fixture
def mock_chat_deps():
    with patch.dict(sys.modules, {
        "PyQt6": MagicMock(),
        "PyQt6.QtWidgets": MagicMock(),
        "PyQt6.QtCore": MagicMock(),
        "PyQt6.QtGui": MagicMock(),
        "py_rme_canary.vis_layer.ui.dialogs.base_modern": MagicMock(),
        "py_rme_canary.vis_layer.ui.theme": MagicMock(),
    }):
        # Mock base class
        mock_modern = sys.modules["py_rme_canary.vis_layer.ui.dialogs.base_modern"]
        class MockModernDialog:
            def __init__(self, *args, **kwargs):
                self.content_layout = MagicMock()
            def setMinimumSize(self, w, h):
                pass
        mock_modern.ModernDialog = MockModernDialog

        # Mock theme manager
        mock_theme = sys.modules["py_rme_canary.vis_layer.ui.theme"]
        tm_instance = MagicMock()
        tm_instance.tokens = {
            "color": {
                "brand": {"primary": "#000", "secondary": "#111"},
                "text": {"primary": "#000", "secondary": "#111", "tertiary": "#222"},
                "surface": {"primary": "#555", "secondary": "#666"},
                "border": {"default": "#777"},
            },
            "radius": {"md": 4, "sm": 2}
        }
        mock_theme.get_theme_manager.return_value = tm_instance

        yield

def test_chat_dialog_escapes_html_injection(mock_chat_deps):
    """Test that ChatDialog escapes HTML in messages to prevent XSS."""
    # Import inside test to use mocked modules
    # Use reload in case it was already imported?
    # Usually pytest isolation handles this if we didn't import at top level.
    import py_rme_canary.vis_layer.ui.dialogs.chat_dialog
    import importlib
    importlib.reload(py_rme_canary.vis_layer.ui.dialogs.chat_dialog)
    from py_rme_canary.vis_layer.ui.dialogs.chat_dialog import ChatDialog

    dialog = ChatDialog()

    # Mock history widget
    dialog.history = MagicMock()

    sender = "<b>Attacker</b>"
    text = "<script>alert('XSS')</script>"
    timestamp = "12:00"

    dialog.append_message(sender, text, timestamp)

    # Verify append was called
    assert dialog.history.append.called

    # Get the HTML string passed to append
    args, _ = dialog.history.append.call_args
    html_content = args[0]

    # Verify sender is escaped
    assert "&lt;b&gt;Attacker&lt;/b&gt;" in html_content
    assert "<b>Attacker</b>" not in html_content

    # Verify text is escaped (note: html.escape also escapes quotes)
    assert "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;" in html_content
    assert "<script>" not in html_content
