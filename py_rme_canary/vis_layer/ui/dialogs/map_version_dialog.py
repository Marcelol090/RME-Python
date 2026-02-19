"""Map Version Changer Dialog.

Dedicated dialog for changing the OTBM version of a loaded map.
Mirrors legacy C++ ``editor/operations/map_version_changer.cpp``.

Provides:
- Current version display
- Target version selector (OTBM 1-6)
- Pre-conversion analysis with warnings
- One-click conversion with undo support
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.database.id_mapper import IdMapper

logger = logging.getLogger(__name__)


# OTBM version descriptions matching C++ MapVersionID enum
OTBM_VERSIONS = {
    0: "OTBM 1 — Tibia 7.4 (ServerID)",
    1: "OTBM 2 — Tibia 8.0 (ServerID)",
    2: "OTBM 3 — Tibia 8.4+ (ServerID)",
    3: "OTBM 4 — Tibia 8.7+ (ServerID)",
    4: "OTBM 5 — Modern (ClientID)",
    5: "OTBM 6 — Modern Extended (ClientID)",
}


class _InfoCard(QFrame):
    """Small info card with label + value."""

    def __init__(self, label: str, value: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        c = get_theme_manager().tokens["color"]

        la = QHBoxLayout(self)
        la.setContentsMargins(12, 8, 12, 8)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {c['text']['secondary']}; font-weight: 600;")
        la.addWidget(lbl)
        la.addStretch()

        self._val = QLabel(value)
        self._val.setStyleSheet(f"color: {c['text']['primary']}; font-weight: 700;")
        la.addWidget(self._val)

        self.setStyleSheet(
            f"_InfoCard {{ background: {c['surface']['secondary']}; "
            f"border: 1px solid {c['border']['primary']}; border-radius: 6px; }}"
        )

    def set_value(self, v: str) -> None:
        self._val.setText(v)


class MapVersionDialog(QDialog):
    """Dialog to change the OTBM version of the current map.

    Parameters
    ----------
    game_map
        The currently loaded GameMap.
    id_mapper
        Optional IdMapper for ClientID conversion analysis.
    parent
        Parent widget.
    """

    def __init__(
        self,
        game_map: GameMap,
        id_mapper: IdMapper | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._game_map = game_map
        self._id_mapper = id_mapper
        self._target_version: int | None = None

        self.setWindowTitle("Change Map OTBM Version")
        self.setMinimumWidth(480)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()

    # -- public --

    @property
    def target_version(self) -> int | None:
        """Selected target version after accept, or None."""
        return self._target_version

    # -- UI setup --

    def _setup_ui(self) -> None:
        c = get_theme_manager().tokens["color"]
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("Change OTBM Version")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {c['text']['primary']};")
        lay.addWidget(title)

        # Description
        desc = QLabel(
            "Convert the map between ServerID (OTBM 1-4) and "
            "ClientID (OTBM 5-6) formats. Items are translated "
            "automatically during save using items.otb mappings."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {c['text']['secondary']}; font-size: 12px;")
        lay.addWidget(desc)

        # Current version card
        cur_ver = int(getattr(self._game_map.header, "otbm_version", 0))
        self._cur_card = _InfoCard("Current Version", OTBM_VERSIONS.get(cur_ver, f"OTBM {cur_ver}"))
        lay.addWidget(self._cur_card)

        # Target version combo
        combo_frame = QFrame()
        combo_lay = QHBoxLayout(combo_frame)
        combo_lay.setContentsMargins(0, 0, 0, 0)

        combo_lbl = QLabel("Target Version:")
        combo_lbl.setStyleSheet(f"color: {c['text']['secondary']}; font-weight: 600;")
        combo_lay.addWidget(combo_lbl)

        self._combo = QComboBox()
        for ver, desc_text in OTBM_VERSIONS.items():
            self._combo.addItem(desc_text, ver)
        # Pre-select a sensible target
        self._combo.setCurrentIndex(max(0, min(cur_ver + 1, len(OTBM_VERSIONS) - 1)))
        self._combo.currentIndexChanged.connect(self._on_version_changed)
        combo_lay.addWidget(self._combo, 1)
        lay.addWidget(combo_frame)

        # Analysis label
        self._analysis_label = QLabel()
        self._analysis_label.setWordWrap(True)
        self._analysis_label.setStyleSheet(f"color: {c['text']['secondary']}; font-size: 11px;")
        lay.addWidget(self._analysis_label)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        self._ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_btn.setText("Convert")
        lay.addWidget(buttons)

        # Initial analysis
        self._on_version_changed()

    def _apply_style(self) -> None:
        c = get_theme_manager().tokens["color"]
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {c['surface']['primary']};
            }}
            QComboBox {{
                background: {c['surface']['secondary']};
                border: 1px solid {c['border']['primary']};
                border-radius: 6px;
                padding: 6px 10px;
                color: {c['text']['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background: {c['surface']['secondary']};
                border: 1px solid {c['border']['secondary']};
                color: {c['text']['primary']};
                selection-background-color: {c['brand']['primary']};
            }}
            QPushButton {{
                background: {c['brand']['primary']};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {c['brand']['secondary']};
            }}
            QPushButton:disabled {{
                background: {c['surface']['tertiary']};
                color: {c['text']['disabled']};
            }}
        """
        )

    # -- handlers --

    def _on_version_changed(self) -> None:
        """Run pre-conversion analysis when target version changes."""
        target = self._combo.currentData()
        cur = int(getattr(self._game_map.header, "otbm_version", 0))
        c = get_theme_manager().tokens["color"]

        if target == cur:
            self._analysis_label.setText("⚠️  Target is the same as current version.")
            self._analysis_label.setStyleSheet(f"color: {c['state']['warning']}; font-size: 11px;")
            self._ok_btn.setEnabled(False)
            return

        # Run analysis
        try:
            from py_rme_canary.logic_layer.map_format_conversion import (
                analyze_map_format_conversion,
            )

            report = analyze_map_format_conversion(self._game_map, target_version=target, id_mapper=self._id_mapper)
            if report.ok:
                self._analysis_label.setText(f"✅  Ready to convert. {report.total_items} items will be processed.")
                self._analysis_label.setStyleSheet(f"color: {c['state']['success']}; font-size: 11px;")
                self._ok_btn.setEnabled(True)
            else:
                issues: list[str] = []
                if report.id_mapper_missing:
                    issues.append("ID mapper not loaded — cannot translate IDs")
                if report.missing_mappings:
                    issues.append(f"{len(report.missing_mappings)} items have no ID mapping")
                if report.placeholder_items:
                    issues.append(f"{report.placeholder_items} placeholder items found")
                self._analysis_label.setText("⚠️  " + "; ".join(issues))
                self._analysis_label.setStyleSheet(f"color: {c['state']['warning']}; font-size: 11px;")
                self._ok_btn.setEnabled(True)  # Allow with warnings
        except Exception:
            logger.exception("Analysis failed")
            self._analysis_label.setText("❌  Analysis failed — see log.")
            self._analysis_label.setStyleSheet(f"color: {c['state']['error']}; font-size: 11px;")
            self._ok_btn.setEnabled(False)

    def _on_accept(self) -> None:
        """Apply the version change."""
        target = self._combo.currentData()
        cur = int(getattr(self._game_map.header, "otbm_version", 0))

        confirm = QMessageBox.question(
            self,
            "Confirm Version Change",
            f"Convert map from OTBM {cur} to OTBM {target}?\n\n"
            "This changes how items are saved (ServerID ↔ ClientID).\n"
            "You can undo this with Ctrl+Z.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            from py_rme_canary.logic_layer.map_format_conversion import (
                apply_map_format_version,
            )

            apply_map_format_version(self._game_map, target_version=target)
            self._target_version = target
            logger.info("Map version changed from OTBM %d to OTBM %d", cur, target)
            self.accept()
        except Exception:
            logger.exception("Version change failed")
            QMessageBox.critical(self, "Error", "Failed to change map version. See log for details.")

    # -- static helper --

    @staticmethod
    def change_version(
        game_map: GameMap,
        id_mapper: IdMapper | None = None,
        parent: QWidget | None = None,
    ) -> int | None:
        """Show the dialog and return the new version, or None if cancelled."""
        dlg = MapVersionDialog(game_map, id_mapper, parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.target_version
        return None
