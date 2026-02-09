from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True, slots=True)
class ClientDataLoadConfig:
    assets_path: str
    prefer_kind: str
    client_version_hint: int
    items_otb_path: str
    items_xml_path: str
    show_summary: bool


class ClientDataLoaderDialog(QDialog):
    """Interactive loader for client assets + map definitions."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        default_assets_path: str = "",
        default_client_version: int = 0,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Load Client Data")
        self.setModal(True)
        self.setMinimumWidth(700)
        self._default_assets_path = str(default_assets_path or "").strip()
        self._default_client_version = int(default_client_version or 0)
        self._setup_ui()
        self._load_defaults()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        intro = QLabel(
            "Load client data stack for map rendering and editing.\n"
            "The loader will validate and integrate sprites, appearances, items.otb, and items.xml."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setSpacing(8)

        self._assets_path_edit = QLineEdit()
        self._assets_path_edit.setPlaceholderText("Client folder or assets folder")
        assets_row = QHBoxLayout()
        assets_row.addWidget(self._assets_path_edit, 1)
        browse_assets = QPushButton("Browse...")
        browse_assets.clicked.connect(self._browse_assets_path)
        assets_row.addWidget(browse_assets)
        assets_host = QWidget()
        assets_host.setLayout(assets_row)
        form.addRow("Client path:", assets_host)

        self._prefer_kind = QComboBox()
        self._prefer_kind.addItem("Auto-detect", "auto")
        self._prefer_kind.addItem("Modern (assets + appearances.dat)", "modern")
        self._prefer_kind.addItem("Legacy (.dat/.spr)", "legacy")
        form.addRow("Asset mode:", self._prefer_kind)

        self._client_version_hint = QSpinBox()
        self._client_version_hint.setRange(0, 100000)
        self._client_version_hint.setToolTip("Optional version hint. Use 0 for automatic context.")
        form.addRow("Client version hint:", self._client_version_hint)

        self._items_otb_edit = QLineEdit()
        self._items_otb_edit.setPlaceholderText("Optional explicit items.otb path")
        otb_row = QHBoxLayout()
        otb_row.addWidget(self._items_otb_edit, 1)
        browse_otb = QPushButton("Browse...")
        browse_otb.clicked.connect(self._browse_items_otb)
        otb_row.addWidget(browse_otb)
        otb_host = QWidget()
        otb_host.setLayout(otb_row)
        form.addRow("items.otb:", otb_host)

        self._items_xml_edit = QLineEdit()
        self._items_xml_edit.setPlaceholderText("Optional explicit items.xml path")
        xml_row = QHBoxLayout()
        xml_row.addWidget(self._items_xml_edit, 1)
        browse_xml = QPushButton("Browse...")
        browse_xml.clicked.connect(self._browse_items_xml)
        xml_row.addWidget(browse_xml)
        xml_host = QWidget()
        xml_host.setLayout(xml_row)
        form.addRow("items.xml:", xml_host)

        root.addLayout(form)

        options_grid = QGridLayout()
        options_grid.setHorizontalSpacing(8)
        options_grid.setVerticalSpacing(6)

        self._show_summary_combo = QComboBox()
        self._show_summary_combo.addItem("Show completion summary", True)
        self._show_summary_combo.addItem("Silent load (status bar only)", False)
        options_grid.addWidget(QLabel("Completion feedback:"), 0, 0)
        options_grid.addWidget(self._show_summary_combo, 0, 1)
        options_grid.setColumnStretch(1, 1)
        root.addLayout(options_grid)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self._accept_with_validation)
        load_btn.setDefault(True)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(load_btn)
        root.addLayout(buttons)

    def _load_defaults(self) -> None:
        self._assets_path_edit.setText(self._default_assets_path)
        self._client_version_hint.setValue(int(self._default_client_version))

    def _browse_assets_path(self) -> None:
        current = self._assets_path_edit.text().strip()
        selected = QFileDialog.getExistingDirectory(self, "Select Client Folder", current)
        if selected:
            self._assets_path_edit.setText(str(selected))

    def _browse_items_otb(self) -> None:
        current = self._items_otb_edit.text().strip()
        path, _ = QFileDialog.getOpenFileName(self, "Select items.otb", current, "OTB files (*.otb);;All files (*.*)")
        if path:
            self._items_otb_edit.setText(str(path))

    def _browse_items_xml(self) -> None:
        current = self._items_xml_edit.text().strip()
        path, _ = QFileDialog.getOpenFileName(self, "Select items.xml", current, "XML files (*.xml);;All files (*.*)")
        if path:
            self._items_xml_edit.setText(str(path))

    def _accept_with_validation(self) -> None:
        cfg = self.config()
        if not cfg.assets_path:
            QMessageBox.warning(self, "Load Client Data", "Client path cannot be empty.")
            return
        if not Path(cfg.assets_path).exists():
            QMessageBox.warning(self, "Load Client Data", f"Client path does not exist:\n{cfg.assets_path}")
            return
        if cfg.items_otb_path and not Path(cfg.items_otb_path).is_file():
            QMessageBox.warning(self, "Load Client Data", f"Invalid items.otb path:\n{cfg.items_otb_path}")
            return
        if cfg.items_xml_path and not Path(cfg.items_xml_path).is_file():
            QMessageBox.warning(self, "Load Client Data", f"Invalid items.xml path:\n{cfg.items_xml_path}")
            return
        self.accept()

    def config(self) -> ClientDataLoadConfig:
        return ClientDataLoadConfig(
            assets_path=str(self._assets_path_edit.text() or "").strip(),
            prefer_kind=str(self._prefer_kind.currentData() or "auto"),
            client_version_hint=int(self._client_version_hint.value()),
            items_otb_path=str(self._items_otb_edit.text() or "").strip(),
            items_xml_path=str(self._items_xml_edit.text() or "").strip(),
            show_summary=bool(self._show_summary_combo.currentData()),
        )
