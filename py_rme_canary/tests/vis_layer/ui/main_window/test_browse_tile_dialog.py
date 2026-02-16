
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
    def findChildren(self, type_): return []
    def add_button(self, text, callback=None, role="secondary"):
        btn = MagicMock()
        btn.text = text
        if callback:
            # Simulate connection
            pass
        btn.setEnabled = MagicMock()
        btn.isEnabled.return_value = True
        return btn
    def add_spacer_to_footer(self): pass
    def setStyleSheet(self, style): pass

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
        super().__init__()
    def count(self):
        return 0

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
mock_qt_widgets.QDialogButtonBox.StandardButton.Close = 1
mock_qt_widgets.QDialogButtonBox.StandardButton.Ok = 2
mock_qt_widgets.QDialogButtonBox.StandardButton.Cancel = 3

# Mock QListWidget enums
mock_qt_widgets.QListWidget.SelectionMode = MagicMock()
mock_qt_widgets.QListWidget.SelectionMode.ExtendedSelection = 1

# Mock Qt.ItemDataRole
mock_qt_core.Qt.ItemDataRole.UserRole = 1
mock_qt_core.Qt.MouseButton.LeftButton = 1

# Mock GameMap and Tile
sys.modules["py_rme_canary.core.data.tile"] = MagicMock()
sys.modules["py_rme_canary.core.database.items_database"] = MagicMock()

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
from py_rme_canary.vis_layer.ui.main_window.browse_tile_dialog import BrowseTileDialog

@pytest.fixture
def mock_tile():
    tile = MagicMock()
    tile.x = 100
    tile.y = 100
    tile.z = 7
    tile.ground = MagicMock()
    tile.ground.id = 100
    tile.items = []
    return tile

@pytest.fixture
def mock_items_db():
    db = MagicMock()
    db.get_item_type.return_value.name = "Test Item"
    return db

def test_browse_tile_dialog_initialization(mock_tile, mock_items_db):
    """Test that BrowseTileDialog initializes correctly with default widgets."""
    dialog = BrowseTileDialog(tile=mock_tile, items_db=mock_items_db)

    # Check window title
    assert dialog.windowTitle() == "Browse Tile"

    # Check if key widgets exist
    assert hasattr(dialog, "_items_list")
    assert hasattr(dialog, "_remove_btn")
    assert hasattr(dialog, "_properties_btn")

def test_browse_tile_dialog_items_list(mock_tile, mock_items_db):
    """Test that items list is populated."""
    # Add some items to tile
    item1 = MagicMock()
    item1.id = 200
    mock_tile.items = [item1]

    dialog = BrowseTileDialog(tile=mock_tile, items_db=mock_items_db)

    # Check if list has items
    # _items_list is a MockWidget, addItem is called
    assert dialog._items_list.addItem.call_count == 2 # Ground + 1 item
