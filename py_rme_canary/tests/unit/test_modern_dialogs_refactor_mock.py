"""Unit tests for modern dialogs refactoring with mocked PyQt6."""
from __future__ import annotations
import sys
from unittest.mock import MagicMock

# Mock PyQt6 before importing any application code
if "PyQt6" not in sys.modules:
    mock_qt = MagicMock()
    sys.modules["PyQt6"] = mock_qt
    sys.modules["PyQt6.QtCore"] = mock_qt.QtCore
    sys.modules["PyQt6.QtGui"] = mock_qt.QtGui
    sys.modules["PyQt6.QtWidgets"] = mock_qt.QtWidgets

    # Define QDialog base class for mocks to inherit
    class MockQDialog:
        DialogCode = MagicMock()
        DialogCode.Accepted = 1

        def __init__(self, parent=None):
            pass
        def setWindowTitle(self, title):
            self._window_title = title
        def windowTitle(self):
            return getattr(self, "_window_title", "")
        def setModal(self, modal):
            pass
        def setMinimumSize(self, w, h):
            pass
        def setMinimumWidth(self, w):
            pass
        def exec(self):
            return 1 # Accepted
        def accept(self):
            pass
        def reject(self):
            pass
        def setWindowFlags(self, flags):
            pass
        def setAttribute(self, attr):
            pass
        def setStyleSheet(self, style):
            pass
        def setLayout(self, layout):
            pass
        def frameGeometry(self):
            return MagicMock()
        def geometry(self):
            return MagicMock()
        def mapFrom(self, w, p):
            return p
        def move(self, p):
            pass

    mock_qt.QtWidgets.QDialog = MockQDialog
    mock_qt.QtWidgets.QWidget = MagicMock()
    mock_qt.QtWidgets.QFrame = MagicMock()

    # Mock Layouts
    class MockLayout(MagicMock):
        def __init__(self, *args, **kwargs):
            super().__init__()
        def count(self): return 0
        def addWidget(self, *args, **kwargs): pass
        def addLayout(self, *args, **kwargs): pass
        def addStretch(self): pass
        def setContentsMargins(self, l, t, r, b): pass
        def setSpacing(self, s): pass

    mock_qt.QtWidgets.QVBoxLayout = MockLayout
    mock_qt.QtWidgets.QHBoxLayout = MockLayout
    mock_qt.QtWidgets.QFormLayout = MockLayout
    mock_qt.QtWidgets.QGridLayout = MockLayout

    mock_qt.QtWidgets.QLabel = MagicMock()
    mock_qt.QtWidgets.QPushButton = MagicMock()
    mock_qt.QtWidgets.QComboBox = MagicMock()
    mock_qt.QtWidgets.QLineEdit = MagicMock()
    mock_qt.QtWidgets.QSpinBox = MagicMock()
    mock_qt.QtWidgets.QCheckBox = MagicMock()
    mock_qt.QtWidgets.QTableWidget = MagicMock()
    mock_qt.QtWidgets.QTableWidgetItem = MagicMock()
    mock_qt.QtWidgets.QProgressBar = MagicMock()
    mock_qt.QtWidgets.QMessageBox = MagicMock()
    mock_qt.QtWidgets.QFileDialog = MagicMock()
    mock_qt.QtWidgets.QGroupBox = MagicMock()
    mock_qt.QtWidgets.QDialogButtonBox = MagicMock()
    mock_qt.QtWidgets.QListWidget = MagicMock()
    mock_qt.QtWidgets.QListWidgetItem = MagicMock()
    mock_qt.QtWidgets.QAbstractItemView = MagicMock()

    mock_qt.QtCore.Qt.WindowType.Dialog = 1
    mock_qt.QtCore.Qt.WindowType.FramelessWindowHint = 2
    mock_qt.QtCore.Qt.WidgetAttribute.WA_TranslucentBackground = 3
    mock_qt.QtCore.Qt.AlignmentFlag.AlignRight = 4
    mock_qt.QtCore.Qt.AlignmentFlag.AlignVCenter = 5
    mock_qt.QtCore.Qt.MouseButton.LeftButton = 1
    mock_qt.QtCore.QPoint = MagicMock

    # QFileDialog.getOpenFileName needs to be static method on mock
    mock_qt.QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=("", ""))
    mock_qt.QtWidgets.QFileDialog.getSaveFileName = MagicMock(return_value=("", ""))
    mock_qt.QtWidgets.QFileDialog.getExistingDirectory = MagicMock(return_value="")

import pytest

class TestModernDialogsRefactorMock:
    """Tests for refactored modern dialog components with mocks."""

    def test_client_profile_edit_dialog_is_modern(self):
        from py_rme_canary.vis_layer.ui.dialogs.client_profiles_dialog import ClientProfileEditDialog
        from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog

        dialog = ClientProfileEditDialog()
        assert isinstance(dialog, ModernDialog)
        assert hasattr(dialog, "content_layout")

    def test_client_profiles_dialog_is_modern(self):
        from py_rme_canary.vis_layer.ui.dialogs.client_profiles_dialog import ClientProfilesDialog
        from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog
        from py_rme_canary.core.config.client_profiles import ClientProfile

        dialog = ClientProfilesDialog(profiles=[], active_profile_id="")
        assert isinstance(dialog, ModernDialog)
        assert hasattr(dialog, "content_layout")

    def test_export_tilesets_dialog_is_modern(self):
        from py_rme_canary.vis_layer.ui.dialogs.export_tilesets_dialog import ExportTilesetsDialog
        from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog

        dialog = ExportTilesetsDialog()
        assert isinstance(dialog, ModernDialog)
        assert hasattr(dialog, "content_layout")

    def test_png_export_dialog_is_modern(self):
        from py_rme_canary.vis_layer.ui.dialogs.png_export_dialog import PNGExportDialog
        from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog

        dialog = PNGExportDialog()
        assert isinstance(dialog, ModernDialog)
        assert hasattr(dialog, "content_layout")
