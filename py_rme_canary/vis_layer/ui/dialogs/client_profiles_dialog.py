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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.core.config.client_profiles import ClientProfile, create_client_profile
from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog


@dataclass(frozen=True, slots=True)
class _ProfileFormData:
    name: str
    client_version: int
    assets_dir: str
    preferred_kind: str


class ClientProfileEditDialog(ModernDialog):
    """Dialog to create or edit a single client profile."""

    def __init__(self, parent: QWidget | None = None, *, profile: ClientProfile | None = None) -> None:
        title = "Edit Client Profile" if profile is not None else "New Client Profile"
        super().__init__(parent, title=title)
        self._profile = profile
        self.setModal(True)
        self.setMinimumWidth(520)
        self._populate_content()
        self._load_profile()

    def _populate_content(self) -> None:
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setSpacing(8)

        self._name = QLineEdit()
        self._name.setPlaceholderText("Example: 10.98-custom")
        form.addRow("Name:", self._name)

        self._client_version = QSpinBox()
        self._client_version.setRange(0, 100000)
        self._client_version.setToolTip("Use 0 for profile-agnostic assets.")
        form.addRow("Client version:", self._client_version)

        assets_row = QHBoxLayout()
        self._assets_dir = QLineEdit()
        self._assets_dir.setPlaceholderText("Path to Tibia client/assets folder")
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse_assets_dir)
        assets_row.addWidget(self._assets_dir, 1)
        assets_row.addWidget(browse)
        assets_host = QWidget()
        assets_host.setLayout(assets_row)
        form.addRow("Assets dir:", assets_host)

        self._preferred_kind = QComboBox()
        self._preferred_kind.addItem("Auto-detect", "auto")
        self._preferred_kind.addItem("Modern (assets/ + appearances)", "modern")
        self._preferred_kind.addItem("Legacy (.dat/.spr)", "legacy")
        form.addRow("Prefer:", self._preferred_kind)

        self.content_layout.addLayout(form)
        self.content_layout.addStretch()

        self.add_spacer_to_footer()
        self.add_button("Cancel", callback=self.reject)
        self.add_button("Save", callback=self._save, role="primary")

    def _load_profile(self) -> None:
        profile = self._profile
        if profile is None:
            return
        self._name.setText(profile.name)
        self._client_version.setValue(int(profile.client_version))
        self._assets_dir.setText(profile.assets_dir)
        idx = self._preferred_kind.findData(profile.preferred_kind)
        self._preferred_kind.setCurrentIndex(max(0, idx))

    def _browse_assets_dir(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Select assets directory")
        if selected:
            self._assets_dir.setText(selected)

    def _save(self) -> None:
        data = self.form_data()
        if not data.name:
            QMessageBox.warning(self, "Client Profile", "Profile name cannot be empty.")
            return
        if not data.assets_dir:
            QMessageBox.warning(self, "Client Profile", "Assets directory cannot be empty.")
            return
        self.accept()

    def form_data(self) -> _ProfileFormData:
        return _ProfileFormData(
            name=str(self._name.text() or "").strip(),
            client_version=int(self._client_version.value()),
            assets_dir=str(self._assets_dir.text() or "").strip(),
            preferred_kind=str(self._preferred_kind.currentData() or "auto"),
        )


class ClientProfilesDialog(ModernDialog):
    """Manage persisted client profiles used by the assets loader."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        profiles: list[ClientProfile],
        active_profile_id: str,
    ) -> None:
        super().__init__(parent, title="Client Profiles")
        self.setModal(True)
        self.setMinimumSize(860, 420)
        self._profiles = list(profiles)
        self._active_profile_id = str(active_profile_id or "")
        if self._profiles and self._active_profile_id not in {p.profile_id for p in self._profiles}:
            self._active_profile_id = self._profiles[0].profile_id
        self._populate_content()
        self._refresh_table()

    def _populate_content(self) -> None:
        help_text = QLabel(
            "Configure reusable assets profiles by client version. "
            "Set one profile as active to be auto-loaded for new maps."
        )
        help_text.setWordWrap(True)
        self.content_layout.addWidget(help_text)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Active", "Name", "Version", "Kind", "Assets Directory"])
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.itemDoubleClicked.connect(self._edit_selected)
        self.content_layout.addWidget(self._table, 1)

        controls = QGridLayout()
        controls.setHorizontalSpacing(8)
        controls.setVerticalSpacing(6)

        self._btn_add = QPushButton("New Profile")
        self._btn_edit = QPushButton("Edit")
        self._btn_delete = QPushButton("Delete")
        self._btn_active = QPushButton("Set Active")

        self._btn_add.clicked.connect(self._add_profile)
        self._btn_edit.clicked.connect(self._edit_selected)
        self._btn_delete.clicked.connect(self._delete_selected)
        self._btn_active.clicked.connect(self._set_active_selected)

        controls.addWidget(self._btn_add, 0, 0)
        controls.addWidget(self._btn_edit, 0, 1)
        controls.addWidget(self._btn_delete, 0, 2)
        controls.addWidget(self._btn_active, 0, 3)
        controls.setColumnStretch(4, 1)
        self.content_layout.addLayout(controls)

        self.add_spacer_to_footer()
        self.add_button("Cancel", callback=self.reject)
        self.add_button("OK", callback=self.accept, role="primary")

    def _refresh_table(self) -> None:
        self._profiles.sort(key=lambda p: (int(p.client_version), p.name.lower(), p.profile_id))
        self._table.setRowCount(len(self._profiles))
        for row, profile in enumerate(self._profiles):
            active_label = "●" if profile.profile_id == self._active_profile_id else ""
            self._table.setItem(row, 0, QTableWidgetItem(active_label))
            self._table.setItem(row, 1, QTableWidgetItem(profile.name))
            self._table.setItem(row, 2, QTableWidgetItem(str(int(profile.client_version))))
            self._table.setItem(row, 3, QTableWidgetItem(profile.preferred_kind))
            self._table.setItem(row, 4, QTableWidgetItem(str(Path(profile.assets_dir))))
        if self._profiles:
            self._table.selectRow(0)

    def _selected_index(self) -> int:
        row = int(self._table.currentRow())
        if 0 <= row < len(self._profiles):
            return row
        return -1

    def _add_profile(self) -> None:
        dialog = ClientProfileEditDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.form_data()
        existing_ids = {item.profile_id for item in self._profiles}
        existing_names = {item.name.lower() for item in self._profiles}
        if data.name.lower() in existing_names:
            QMessageBox.warning(self, "Client Profile", f"A profile named '{data.name}' already exists.")
            return
        try:
            profile = create_client_profile(
                name=data.name,
                client_version=data.client_version,
                assets_dir=data.assets_dir,
                preferred_kind=data.preferred_kind,
                existing_ids=existing_ids,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Client Profile", str(exc))
            return
        self._profiles.append(profile)
        if not self._active_profile_id:
            self._active_profile_id = profile.profile_id
        self._refresh_table()

    def _edit_selected(self) -> None:
        index = self._selected_index()
        if index < 0:
            return
        current = self._profiles[index]
        dialog = ClientProfileEditDialog(self, profile=current)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.form_data()
        existing_names = {item.name.lower() for item in self._profiles if item.profile_id != current.profile_id}
        if data.name.lower() in existing_names:
            QMessageBox.warning(self, "Client Profile", f"A profile named '{data.name}' already exists.")
            return
        try:
            updated = create_client_profile(
                name=data.name,
                client_version=data.client_version,
                assets_dir=data.assets_dir,
                preferred_kind=data.preferred_kind,
                profile_id=current.profile_id,
                existing_ids={item.profile_id for item in self._profiles if item.profile_id != current.profile_id},
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Client Profile", str(exc))
            return
        self._profiles[index] = updated
        self._refresh_table()

    def _delete_selected(self) -> None:
        index = self._selected_index()
        if index < 0:
            return
        profile = self._profiles[index]
        reply = QMessageBox.question(
            self,
            "Delete Client Profile",
            f"Delete profile '{profile.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        del self._profiles[index]
        if profile.profile_id == self._active_profile_id:
            self._active_profile_id = self._profiles[0].profile_id if self._profiles else ""
        self._refresh_table()

    def _set_active_selected(self) -> None:
        index = self._selected_index()
        if index < 0:
            return
        self._active_profile_id = self._profiles[index].profile_id
        self._refresh_table()

    def result_profiles(self) -> list[ClientProfile]:
        return list(self._profiles)

    def result_active_profile_id(self) -> str:
        return str(self._active_profile_id or "")
