"""
Immersive Asset Loader Wizard.

A modern, step-by-step wizard for loading Tibia client assets,
replacing the legacy dialog with a more user-friendly experience.
"""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from py_rme_canary.vis_layer.ui.dialogs.client_data_loader_dialog import ClientDataLoadConfig
from py_rme_canary.vis_layer.ui.theme import get_theme_manager


class AssetLoaderWizard(QWizard):
    """
    Wizard for loading client assets (SPR/DAT/Appearances).
    """

    def __init__(self, parent: QWidget | None = None, defaults: ClientDataLoadConfig | None = None) -> None:
        super().__init__(parent)
        self.defaults = defaults or ClientDataLoadConfig("", "auto", 0, "", "", True)

        self.setWindowTitle("Load Client Assets")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(700, 500)

        # Apply Theme
        self._apply_theme()

        # Add pages
        self.intro_page = IntroPage(self)
        self.client_page = ClientPage(self, self.defaults)
        self.metadata_page = MetadataPage(self, self.defaults)
        self.validation_page = ValidationPage(self)

        self.addPage(self.intro_page)
        self.addPage(self.client_page)
        self.addPage(self.metadata_page)
        self.addPage(self.validation_page)

    def _apply_theme(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]

        # QWizard customization is tricky via stylesheet,
        # but we can style the container.
        self.setStyleSheet(f"""
            QWizard {{
                background-color: {c["surface"]["primary"]};
                color: {c["text"]["primary"]};
            }}
            QLabel {{
                color: {c["text"]["primary"]};
            }}
            QLabel#Title {{
                font-size: 20px;
                font-weight: bold;
                color: {c["brand"]["primary"]};
                margin-bottom: 10px;
            }}
            QLabel#Subtitle {{
                font-size: 14px;
                color: {c["text"]["secondary"]};
                margin-bottom: 20px;
            }}
        """)

    def get_config(self) -> ClientDataLoadConfig:
        """Collect configuration from all pages."""
        return ClientDataLoadConfig(
            assets_path=self.client_page.get_assets_path(),
            prefer_kind=self.client_page.get_prefer_kind(),
            client_version_hint=self.client_page.get_version_hint(),
            items_otb_path=self.metadata_page.get_otb_path(),
            items_xml_path=self.metadata_page.get_xml_path(),
            show_summary=True
        )


class IntroPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Welcome")
        self.setSubTitle("Prepare your mapping environment.")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Asset Loader")
        title.setObjectName("Title")
        layout.addWidget(title)

        desc = QLabel(
            "To edit maps, py_rme_canary needs to load Tibia client assets.\n\n"
            "• Sprites (.spr)\n"
            "• Data (.dat)\n"
            "• Appearances (modern clients)\n"
            "• Item Definitions (items.otb / items.xml)"
        )
        desc.setObjectName("Subtitle")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addStretch()
        self.setLayout(layout)


class ClientPage(QWizardPage):
    def __init__(self, parent=None, defaults: ClientDataLoadConfig = None):
        super().__init__(parent)
        self.setTitle("Client Assets")
        self.setSubTitle("Locate the Tibia client folder.")
        self.defaults = defaults
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Drag & Drop Area
        self.drop_area = DropArea()
        self.drop_area.path_dropped.connect(self._on_path_dropped)
        layout.addWidget(self.drop_area)

        form = QFormLayout()
        form.setSpacing(16)

        # Path Input
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("C:/Tibia/packages/Tibia/assets")
        if self.defaults:
            self.path_edit.setText(self.defaults.assets_path)
        self.path_edit.textChanged.connect(self.completeChanged)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)

        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        form.addRow("Assets Folder:", path_layout)

        # Version Hint
        self.version_spin = QComboBox() # Using Combo for common versions + custom
        common_versions = ["0 (Auto-detect)", "1340", "1330", "1300", "1200", "1100", "1098", "860", "760", "740"]
        self.version_spin.addItems(common_versions)
        self.version_spin.setEditable(True)
        if self.defaults and self.defaults.client_version_hint > 0:
            self.version_spin.setCurrentText(str(self.defaults.client_version_hint))
        form.addRow("Client Version:", self.version_spin)

        # Mode
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Auto-detect", "Modern (appearances.dat)", "Legacy (.dat/.spr)"])
        if self.defaults:
            kind = (self.defaults.prefer_kind or "auto").lower()
            if kind == "modern":
                self.mode_combo.setCurrentIndex(1)
            elif kind == "legacy":
                self.mode_combo.setCurrentIndex(2)
            else:
                self.mode_combo.setCurrentIndex(0)
        form.addRow("Loading Mode:", self.mode_combo)

        layout.addLayout(form)
        self.setLayout(layout)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select Assets Directory", self.path_edit.text())
        if d:
            self.path_edit.setText(d)

    def _on_path_dropped(self, path: str):
        self.path_edit.setText(path)

    def isComplete(self) -> bool:
        path = self.path_edit.text().strip()
        return bool(path and os.path.exists(path))

    def get_assets_path(self) -> str:
        return self.path_edit.text().strip()

    def get_version_hint(self) -> int:
        txt = self.version_spin.currentText().split()[0] # Handle "0 (Auto...)"
        if txt.isdigit():
            return int(txt)
        return 0

    def get_prefer_kind(self) -> str:
        idx = self.mode_combo.currentIndex()
        if idx == 1: return "modern"
        if idx == 2: return "legacy"
        return "auto"


class MetadataPage(QWizardPage):
    def __init__(self, parent=None, defaults: ClientDataLoadConfig = None):
        super().__init__(parent)
        self.setTitle("Item Definitions")
        self.setSubTitle("Optional: Override items.otb or items.xml locations.")
        self.defaults = defaults
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        # OTB
        otb_layout = QHBoxLayout()
        self.otb_edit = QLineEdit()
        self.otb_edit.setPlaceholderText("Leave empty to auto-detect")
        if self.defaults:
            self.otb_edit.setText(self.defaults.items_otb_path)

        otb_btn = QPushButton("Browse...")
        otb_btn.clicked.connect(lambda: self._browse(self.otb_edit, "OTB (*.otb)"))
        otb_layout.addWidget(self.otb_edit)
        otb_layout.addWidget(otb_btn)
        form.addRow("items.otb:", otb_layout)

        # XML
        xml_layout = QHBoxLayout()
        self.xml_edit = QLineEdit()
        self.xml_edit.setPlaceholderText("Leave empty to auto-detect")
        if self.defaults:
            self.xml_edit.setText(self.defaults.items_xml_path)

        xml_btn = QPushButton("Browse...")
        xml_btn.clicked.connect(lambda: self._browse(self.xml_edit, "XML (*.xml)"))
        xml_layout.addWidget(self.xml_edit)
        xml_layout.addWidget(xml_btn)
        form.addRow("items.xml:", xml_layout)

        layout.addLayout(form)

        info = QLabel("Note: The editor will try to find these files automatically in common locations if left empty.")
        info.setStyleSheet("color: gray; margin-top: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.setLayout(layout)

    def _browse(self, edit: QLineEdit, filter: str):
        f, _ = QFileDialog.getOpenFileName(self, "Select File", "", filter)
        if f:
            edit.setText(f)

    def get_otb_path(self) -> str:
        return self.otb_edit.text().strip()

    def get_xml_path(self) -> str:
        return self.xml_edit.text().strip()


class ValidationPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Validation")
        self.setSubTitle("Verifying asset integrity...")

    def initializePage(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_lbl = QLabel("Ready to load.")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_lbl)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedWidth(400)
        layout.addWidget(self.progress)

        self.setLayout(layout)

        # Start fake validation sequence on show
        QTimer.singleShot(500, self._start_validation)

    def _start_validation(self):
        # In a real scenario, this might run the heavy logic.
        # For now, we just simulate a check to let the user review settings.
        self.status_lbl.setText("Checking path existence...")
        self.progress.setValue(20)

        wizard = self.wizard()
        if isinstance(wizard, AssetLoaderWizard):
            path = wizard.client_page.get_assets_path()
            if os.path.exists(path):
                self.status_lbl.setText(f"Found assets at: {os.path.basename(path)}")
                self.progress.setValue(100)
                self.completeChanged.emit()
            else:
                self.status_lbl.setText("Error: Path not found!")
                self.progress.setValue(0)

    def isComplete(self) -> bool:
        return self.progress.value() == 100


class DropArea(QFrame):
    path_dropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #6272A4;
                border-radius: 12px;
                background: rgba(98, 114, 164, 0.1);
            }
            QFrame:hover {
                border-color: #BD93F9;
                background: rgba(189, 147, 249, 0.1);
            }
        """)

        layout = QVBoxLayout(self)
        lbl = QLabel("Drag & Drop Client Folder Here")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #BD93F9;")
        layout.addWidget(lbl)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isdir(path):
                self.path_dropped.emit(path)
