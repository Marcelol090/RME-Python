
import sys
from unittest.mock import MagicMock

# Mock PyQt6 modules BEFORE they are imported by the code under test
mock_qt_widgets = MagicMock()
mock_qt_core = MagicMock()
mock_qt_gui = MagicMock()

sys.modules["PyQt6.QtWidgets"] = mock_qt_widgets
sys.modules["PyQt6.QtCore"] = mock_qt_core
sys.modules["PyQt6.QtGui"] = mock_qt_gui
sys.modules["PyQt6"] = MagicMock()

class MockBase:
    def __init__(self, *args, **kwargs):
        pass
    def __call__(self, *args, **kwargs):
        return MagicMock()

class MockQDialog(MockBase):
    def __init__(self, parent=None, *args, **kwargs):
        pass
    def setWindowTitle(self, title):
        self._window_title = title
    def windowTitle(self):
        return getattr(self, "_window_title", "")
    def setModal(self, modal): pass
    def setMinimumWidth(self, width): pass
    def setMinimumSize(self, w, h): pass
    def setLayout(self, layout): pass
    def setAttribute(self, attr): pass
    def setWindowFlags(self, flags): pass
    def setFixedSize(self, w, h): pass
    def reject(self): pass
    def accept(self): pass
    def exec(self): return 1
    def setStyleSheet(self, style): pass
    def findChildren(self, type_): return []
    def add_button(self, text, callback=None, role="secondary"):
        btn = MagicMock()
        btn.text = text
        if callback:
            # Simulate connection
            pass
        btn.setEnabled = MagicMock()
        # Initial state simulation if needed
        btn.isEnabled.return_value = True
        return btn
    def add_spacer_to_footer(self): pass

    # Mock content_layout property
    @property
    def content_layout(self):
        if not hasattr(self, "_content_layout"):
            self._content_layout = MagicMock()
        return self._content_layout
    @content_layout.setter
    def content_layout(self, val):
        self._content_layout = val


mock_qt_widgets.QDialog = MockQDialog

# Define a generic mock widget class that accepts any args in init
class MockWidget(MagicMock):
    def __init__(self, *args, **kwargs):
        # Don't pass args to MagicMock constructor to avoid spec issues
        super().__init__()

# Assign this class to all widgets
for widget_name in [
    "QButtonGroup", "QCheckBox", "QDialogButtonBox", "QFileDialog",
    "QFormLayout", "QGroupBox", "QHBoxLayout", "QLineEdit", "QPushButton",
    "QRadioButton", "QSpinBox", "QVBoxLayout", "QWidget", "QFrame", "QLabel",
    "QListWidget", "QListWidgetItem", "QGraphicsDropShadowEffect"
]:
    setattr(mock_qt_widgets, widget_name, MockWidget)

# Mock QDialogButtonBox enums
mock_qt_widgets.QDialogButtonBox.StandardButton = MagicMock()
mock_qt_widgets.QDialogButtonBox.StandardButton.Ok = 1
mock_qt_widgets.QDialogButtonBox.StandardButton.Cancel = 2

# Add static methods to QFileDialog class
mock_qt_widgets.QFileDialog.getOpenFileName = MagicMock()

# Mock GameMap
sys.modules["py_rme_canary.core.data.gamemap"] = MagicMock()
sys.modules["py_rme_canary.logic_layer.operations.map_import"] = MagicMock()

# Mock ThemeManager
mock_theme = MagicMock()
sys.modules["py_rme_canary.vis_layer.ui.theme"] = mock_theme
mock_theme.get_theme_manager.return_value.tokens = {
    "color": {
        "surface": {"primary": "#000", "secondary": "#111", "elevated": "#222"},
        "border": {"default": "#000"},
        "text": {"primary": "#000", "secondary": "#555"},
        "brand": {"primary": "#000", "secondary": "#000"},
        "state": {"error": "#000", "hover": "#333", "active": "#444"}
    },
    "radius": {"lg": 10, "sm": 5, "md": 5}
}

import pytest
from py_rme_canary.vis_layer.ui.main_window.import_map_dialog import ImportMapDialog

@pytest.fixture
def mock_gamemap():
    return MagicMock()

def test_import_map_dialog_initialization(mock_gamemap):
    """Test that ImportMapDialog initializes correctly with default widgets."""
    dialog = ImportMapDialog(current_map=mock_gamemap)

    # Check window title
    assert dialog.windowTitle() == "Import Map"

    # Check if key widgets exist
    assert hasattr(dialog, "_file_edit")
    assert hasattr(dialog, "_offset_x_spin")
    assert hasattr(dialog, "_import_tiles_chk")

    # Check new buttons
    assert hasattr(dialog, "_import_btn")
    assert hasattr(dialog, "_cancel_btn")

    # Check initial state of import button
    # Since we mocked setEnabled, check if it was called with False
    dialog._import_btn.setEnabled.assert_called_with(False)

def test_import_map_dialog_browse(mock_gamemap):
    """Test browsing for a file updates the UI."""
    dialog = ImportMapDialog(current_map=mock_gamemap)

    # Mock QFileDialog.getOpenFileName
    mock_file = "/path/to/test.otbm"
    mock_qt_widgets.QFileDialog.getOpenFileName.return_value = (mock_file, "OTBM Files (*.otbm)")

    # Simulate browse
    dialog._browse_file()

    # Check if file path is set
    dialog._file_edit.setText.assert_called_with(mock_file)
    assert str(dialog._import_path) == mock_file

    # Check if import button is enabled
    dialog._import_btn.setEnabled.assert_called_with(True)
