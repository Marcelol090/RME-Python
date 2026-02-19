"""Border Builder Dialog.

UI for viewing and managing border rules for auto-connecting brushes.
Allows users to preview border patterns and configure custom rules.
Supports import/export of legacy RME borders.xml format.

Layer: vis_layer (OK to use PyQt6)
Reference: AutoBorderProcessor in logic_layer/borders/processor.py
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    from py_rme_canary.logic_layer.brush_definitions import BrushDefinition


def _c() -> dict:
    return get_theme_manager().tokens["color"]


def _r() -> dict:
    return get_theme_manager().tokens.get("radius", {})


class BorderPreviewWidget(QFrame):
    """Visual preview of 3x3 neighbor grid with border pattern."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.setMaximumSize(200, 200)
        self._mask = 0
        self._key = "SOLITARY"
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)

    def set_pattern(self, mask: int, key: str) -> None:
        """Set the pattern to display."""
        self._mask = mask
        self._key = key
        self.update()

    def paintEvent(self, event: Any) -> None:
        """Draw the 3x3 preview grid."""
        c = _c()
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cell = min(w, h) // 3

        # Draw grid
        painter.setPen(QPen(QColor(c["border"]["default"]), 1))
        for i in range(4):
            painter.drawLine(i * cell, 0, i * cell, 3 * cell)
            painter.drawLine(0, i * cell, 3 * cell, i * cell)

        # Neighbor positions (N=0, E=1, S=2, W=3)
        neighbors = [
            (1, 0),  # North
            (2, 1),  # East
            (1, 2),  # South
            (0, 1),  # West
        ]

        # Draw center tile (selected)
        painter.setBrush(QColor(c["brand"]["secondary"]))
        painter.drawRect(cell, cell, cell, cell)

        # Draw neighbors based on mask
        for bit, (gx, gy) in enumerate(neighbors):
            if self._mask & (1 << bit):
                painter.setBrush(QColor(c["state"]["success"]))
            else:
                painter.setBrush(QColor(c["surface"]["secondary"]))
            painter.drawRect(gx * cell, gy * cell, cell, cell)

        # Draw key label
        painter.setPen(QColor(c["text"]["primary"]))
        painter.drawText(0, 3 * cell + 5, 3 * cell, 20, Qt.AlignmentFlag.AlignCenter, self._key)
        painter.end()


class BorderPatternList(QFrame):
    """List of all 16 border patterns with their sprite IDs."""

    pattern_selected = pyqtSignal(int, str)  # mask, key

    # Mask to key mapping (from AutoBorderProcessor)
    MASK_TO_KEY: dict[int, str] = {
        0: "SOLITARY",
        1: "END_SOUTH",
        2: "END_WEST",
        3: "CORNER_NE",
        4: "END_NORTH",
        5: "VERTICAL",
        6: "CORNER_SE",
        7: "T_WEST",
        8: "END_EAST",
        9: "CORNER_NW",
        10: "HORIZONTAL",
        11: "T_SOUTH",
        12: "CORNER_SW",
        13: "T_EAST",
        14: "T_NORTH",
        15: "CROSS",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._brush_def: BrushDefinition | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        c = _c()
        r = _r()
        rad_sm = r.get("sm", 4)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Title
        title = QLabel("Border Patterns (16)")
        title.setStyleSheet(f"font-weight: bold; color: {c['text']['primary']};")
        layout.addWidget(title)

        # Pattern list
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            f"""
            QListWidget {{
                background: {c['surface']['primary']};
                border: 1px solid {c['border']['default']};
                border-radius: {rad_sm}px;
            }}
            QListWidget::item {{
                padding: 8px;
                color: {c['text']['primary']};
                border-bottom: 1px solid {c['surface']['secondary']};
            }}
            QListWidget::item:selected {{
                background: {c['brand']['secondary']};
            }}
            QListWidget::item:hover {{
                background: {c['surface']['secondary']};
            }}
        """
        )
        self.list_widget.currentRowChanged.connect(self._on_row_changed)

        # Populate patterns
        for mask in range(16):
            key = self.MASK_TO_KEY[mask]
            item = QListWidgetItem(f"[{mask:04b}] {key}")
            item.setData(Qt.ItemDataRole.UserRole, mask)
            item.setData(Qt.ItemDataRole.UserRole + 1, key)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

    def _on_row_changed(self, row: int) -> None:
        """Emit signal when pattern selected."""
        item = self.list_widget.item(row)
        if item:
            mask = item.data(Qt.ItemDataRole.UserRole)
            key = item.data(Qt.ItemDataRole.UserRole + 1)
            self.pattern_selected.emit(mask, key)

    def set_brush(self, brush_def: BrushDefinition | None) -> None:
        """Update list with brush-specific sprite IDs."""
        self._brush_def = brush_def
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if item is None:
                continue
            mask = item.data(Qt.ItemDataRole.UserRole)
            key = item.data(Qt.ItemDataRole.UserRole + 1)

            sprite_id = "—"
            if brush_def is not None:
                border_val = brush_def.get_border(key)
                if border_val:
                    sprite_id = str(border_val)

            item.setText(f"[{mask:04b}] {key}: {sprite_id}")


class BorderBuilderDialog(QDialog):
    """Dialog for viewing and managing border rules.

    Shows:
    - List of brushes with borders
    - 16 border patterns with sprite IDs
    - Visual pattern preview
    - Brush configuration
    """

    def __init__(self, brush_manager: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.brush_manager = brush_manager
        self._current_brush: BrushDefinition | None = None
        self._current_pattern_key: str | None = None

        self.setWindowTitle("Border Builder")
        self.setMinimumSize(800, 600)
        self.setModal(False)

        self._setup_ui()
        self._apply_style()
        self._load_saved_overrides()
        self._load_brushes()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        c = _c()
        r = _r()
        rad_sm = r.get("sm", 4)
        rad = r.get("md", 6)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("Border Builder")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {c['text']['primary']};")
        layout.addWidget(title)

        description = QLabel(
            "View and manage border patterns for auto-connecting brushes. "
            "Select a brush to see, edit, and persist border sprite mappings."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {c['text']['secondary']}; margin-bottom: 8px;")
        layout.addWidget(description)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Brush list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        brush_label = QLabel("Brushes with Borders")
        brush_label.setStyleSheet(f"font-weight: bold; color: {c['text']['primary']};")
        left_layout.addWidget(brush_label)

        self.brush_list = QListWidget()
        self.brush_list.setStyleSheet(
            f"""
            QListWidget {{
                background: {c['surface']['primary']};
                border: 1px solid {c['border']['default']};
                border-radius: {rad_sm}px;
            }}
            QListWidget::item {{
                padding: 8px;
                color: {c['text']['primary']};
            }}
            QListWidget::item:selected {{
                background: {c['brand']['secondary']};
            }}
        """
        )
        self.brush_list.currentItemChanged.connect(self._on_brush_selected)
        left_layout.addWidget(self.brush_list)

        splitter.addWidget(left_panel)

        # Center panel - Pattern list
        self.pattern_list = BorderPatternList()
        self.pattern_list.pattern_selected.connect(self._on_pattern_selected)
        splitter.addWidget(self.pattern_list)

        # Right panel - Preview and info
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        group_qss = f"""
            QGroupBox {{
                color: {c['text']['primary']};
                font-weight: bold;
                border: 1px solid {c['border']['default']};
                border-radius: {rad_sm}px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """

        # Preview
        preview_group = QGroupBox("Pattern Preview")
        preview_group.setStyleSheet(group_qss)
        preview_layout = QVBoxLayout(preview_group)

        self.preview_widget = BorderPreviewWidget()
        preview_layout.addWidget(self.preview_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        right_layout.addWidget(preview_group)

        # Brush info
        info_group = QGroupBox("Brush Info")
        info_group.setStyleSheet(group_qss)
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(8)

        lbl_qss = f"color: {c['text']['primary']};"

        self.info_name = QLabel("—")
        self.info_name.setStyleSheet(lbl_qss)
        info_layout.addRow("Name:", self.info_name)

        self.info_type = QLabel("—")
        self.info_type.setStyleSheet(lbl_qss)
        info_layout.addRow("Type:", self.info_type)

        self.info_server_id = QLabel("—")
        self.info_server_id.setStyleSheet(lbl_qss)
        info_layout.addRow("Server ID:", self.info_server_id)

        self.info_border_count = QLabel("—")
        self.info_border_count.setStyleSheet(lbl_qss)
        info_layout.addRow("Borders:", self.info_border_count)

        right_layout.addWidget(info_group)

        # Rule editor
        editor_group = QGroupBox("Rule Editor")
        editor_group.setStyleSheet(group_qss)
        editor_layout = QFormLayout(editor_group)
        editor_layout.setSpacing(8)

        self.rule_pattern = QLabel("—")
        self.rule_pattern.setStyleSheet(lbl_qss)
        editor_layout.addRow("Pattern:", self.rule_pattern)

        self.rule_item_id = QSpinBox()
        self.rule_item_id.setRange(0, 2_147_483_647)
        self.rule_item_id.setToolTip("Set to 0 to clear this pattern mapping")
        editor_layout.addRow("Border Item ID:", self.rule_item_id)

        buttons_row = QHBoxLayout()
        self.btn_apply_rule = QPushButton("Apply Rule")
        self.btn_apply_rule.clicked.connect(self._apply_rule)
        buttons_row.addWidget(self.btn_apply_rule)

        self.btn_clear_rule = QPushButton("Clear Rule")
        self.btn_clear_rule.clicked.connect(self._clear_rule)
        buttons_row.addWidget(self.btn_clear_rule)
        editor_layout.addRow("", buttons_row)

        save_row = QHBoxLayout()
        self.btn_save_overrides = QPushButton("Save Overrides")
        self.btn_save_overrides.clicked.connect(self._save_overrides)
        save_row.addWidget(self.btn_save_overrides)

        self.btn_reload_overrides = QPushButton("Reload Overrides")
        self.btn_reload_overrides.clicked.connect(self._reload_overrides)
        save_row.addWidget(self.btn_reload_overrides)
        editor_layout.addRow("", save_row)

        right_layout.addWidget(editor_group)

        self.message_label = QLabel("")
        self.message_label.setStyleSheet(f"color: {c['text']['secondary']};")
        self.message_label.setWordWrap(True)
        right_layout.addWidget(self.message_label)

        right_layout.addStretch()

        splitter.addWidget(right_panel)

        # Set splitter sizes
        splitter.setSizes([200, 300, 300])
        layout.addWidget(splitter)

        # Bottom buttons
        button_layout = QHBoxLayout()

        self.btn_import_xml = QPushButton("Import borders.xml")
        self.btn_import_xml.setToolTip("Import border definitions from a legacy RME borders.xml file")
        self.btn_import_xml.clicked.connect(self._import_borders_xml)
        button_layout.addWidget(self.btn_import_xml)

        self.btn_export_xml = QPushButton("Export borders.xml")
        self.btn_export_xml.setToolTip("Export current border definitions to legacy RME borders.xml format")
        self.btn_export_xml.clicked.connect(self._export_borders_xml)
        button_layout.addWidget(self.btn_export_xml)

        button_layout.addStretch()

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_close)

        layout.addLayout(button_layout)

    def _apply_style(self) -> None:
        """Apply modern dark styling."""
        c = _c()
        r = _r()
        rad = r.get("md", 6)

        self.setStyleSheet(
            f"""
            QDialog {{
                background: {c['surface']['primary']};
            }}
            QLabel {{
                color: {c['text']['secondary']};
            }}
            QPushButton {{
                background: {c['surface']['tertiary']};
                color: {c['text']['primary']};
                border: 1px solid {c['border']['strong']};
                border-radius: {rad}px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background: {c['surface']['hover']};
                border-color: {c['brand']['secondary']};
            }}
        """
        )

    def _load_brushes(self) -> None:
        """Load brushes that have border definitions."""
        if self.brush_manager is None:
            return

        # Get all brushes with borders
        brushes = getattr(self.brush_manager, "all_brushes", None)
        if brushes is None:
            brushes = getattr(self.brush_manager, "_brushes", {})

        if callable(brushes):
            brushes = brushes()

        if isinstance(brushes, dict):
            brushes = brushes.values()

        for brush in brushes:
            if brush is None:
                continue
            borders = getattr(brush, "borders", None)
            if borders and len(borders) > 0:
                name = getattr(brush, "name", None) or str(getattr(brush, "server_id", "?"))
                brush_type = getattr(brush, "brush_type", "unknown")
                getattr(brush, "server_id", 0)

                item = QListWidgetItem(f"[{brush_type}] {name}")
                item.setData(Qt.ItemDataRole.UserRole, brush)
                self.brush_list.addItem(item)

        if self.brush_list.count() > 0:
            self.brush_list.setCurrentRow(0)
        if self.pattern_list.list_widget.count() > 0:
            self.pattern_list.list_widget.setCurrentRow(0)

    def _on_brush_selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        """Handle brush selection."""
        if current is None:
            self.pattern_list.set_brush(None)
            self._update_info(None)
            self._current_brush = None
            self._refresh_rule_editor()
            return

        brush = current.data(Qt.ItemDataRole.UserRole)
        self._current_brush = brush
        self.pattern_list.set_brush(brush)
        self._update_info(brush)
        self._refresh_rule_editor()

    def _update_info(self, brush: Any) -> None:
        """Update brush info panel."""
        if brush is None:
            self.info_name.setText("—")
            self.info_type.setText("—")
            self.info_server_id.setText("—")
            self.info_border_count.setText("—")
            return

        name = getattr(brush, "name", None) or "Unnamed"
        brush_type = getattr(brush, "brush_type", "unknown")
        server_id = getattr(brush, "server_id", 0)
        borders = getattr(brush, "borders", {})

        self.info_name.setText(str(name))
        self.info_type.setText(str(brush_type))
        self.info_server_id.setText(str(server_id))
        self.info_border_count.setText(f"{len(borders)} defined")

    def _on_pattern_selected(self, mask: int, key: str) -> None:
        """Handle pattern selection in list."""
        self._current_pattern_key = str(key)
        self.preview_widget.set_pattern(mask, key)
        self._refresh_rule_editor()

    def _refresh_rule_editor(self) -> None:
        brush = self._current_brush
        key = self._current_pattern_key
        enabled = bool(brush is not None and key)

        self.btn_apply_rule.setEnabled(enabled)
        self.btn_clear_rule.setEnabled(enabled)
        self.rule_item_id.setEnabled(enabled)

        if not enabled:
            self.rule_pattern.setText("—")
            self.rule_item_id.setValue(0)
            return

        assert key is not None
        self.rule_pattern.setText(str(key))
        border_id = getattr(brush, "get_border", lambda _k: None)(str(key))
        self.rule_item_id.setValue(int(border_id) if border_id is not None else 0)

    def _reload_current_brush(self) -> None:
        brush = self._current_brush
        if brush is None:
            return
        get_brush = getattr(self.brush_manager, "get_brush", None)
        if not callable(get_brush):
            return
        fresh = get_brush(int(getattr(brush, "server_id", 0)))
        if fresh is None:
            return
        self._current_brush = fresh
        row = self.brush_list.currentRow()
        current_item = self.brush_list.item(row) if row >= 0 else None
        if current_item is not None:
            current_item.setData(Qt.ItemDataRole.UserRole, fresh)
        self.pattern_list.set_brush(fresh)
        self._update_info(fresh)
        self._refresh_rule_editor()

    def _set_message(self, message: str) -> None:
        self.message_label.setText(str(message))
        parent = self.parent()
        status = getattr(parent, "status", None) if parent is not None else None
        if status is not None and hasattr(status, "showMessage"):
            with contextlib.suppress(Exception):
                status.showMessage(str(message))

    def _apply_rule(self) -> None:
        brush = self._current_brush
        key = self._current_pattern_key
        if brush is None or not key:
            return

        setter = getattr(self.brush_manager, "set_border_override", None)
        if not callable(setter):
            self._set_message("Current brush manager does not support border editing.")
            return

        border_id = int(self.rule_item_id.value())
        changed = bool(
            setter(
                int(getattr(brush, "server_id", 0)),
                str(key),
                int(border_id) if border_id > 0 else None,
            )
        )
        if not changed:
            self._set_message("No changes applied.")
            return

        self._reload_current_brush()
        server_id = int(getattr(self._current_brush, "server_id", 0))
        self._set_message(f"Rule {str(key)} updated for brush #{server_id}.")
        parent = self.parent()
        canvas = getattr(parent, "canvas", None) if parent is not None else None
        if canvas is not None and hasattr(canvas, "update"):
            with contextlib.suppress(Exception):
                canvas.update()

    def _clear_rule(self) -> None:
        self.rule_item_id.setValue(0)
        self._apply_rule()

    def _load_saved_overrides(self) -> None:
        loader = getattr(self.brush_manager, "load_border_overrides_file", None)
        if not callable(loader):
            return
        try:
            changed = int(loader())
        except Exception as exc:
            self._set_message(f"Failed to load border overrides: {exc}")
            return
        if changed > 0:
            self._set_message(f"Loaded {changed} border override(s).")

    def _save_overrides(self) -> None:
        saver = getattr(self.brush_manager, "save_border_overrides_file", None)
        if not callable(saver):
            self._set_message("Current brush manager does not support persisted overrides.")
            return
        try:
            target = saver()
        except Exception as exc:
            QMessageBox.critical(self, "Border Builder", f"Failed to save overrides:\n{exc}")
            return
        if target is None:
            self._set_message("No override path available.")
            return
        self._set_message(f"Overrides saved to {target}.")

    def _reload_overrides(self) -> None:
        loader = getattr(self.brush_manager, "load_border_overrides_file", None)
        if not callable(loader):
            self._set_message("Current brush manager does not support persisted overrides.")
            return
        try:
            changed = int(loader())
        except Exception as exc:
            QMessageBox.critical(self, "Border Builder", f"Failed to reload overrides:\n{exc}")
            return
        self._reload_current_brush()
        self._set_message(f"Reloaded overrides ({changed} brush(es) changed).")

    # ── Legacy borders.xml import/export ────────────────────────────────────

    def _import_borders_xml(self) -> None:
        """Import border definitions from a legacy RME borders.xml file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Legacy borders.xml",
            "",
            "XML files (*.xml);;All files (*)",
        )
        if not path:
            return

        try:
            from py_rme_canary.logic_layer.borders.borders_xml_io import (
                import_borders_into_manager,
                parse_borders_xml,
            )

            borders = parse_borders_xml(path)
            if not borders:
                self._set_message("No border definitions found in the selected file.")
                return

            changed = import_borders_into_manager(self.brush_manager, borders)
            self._reload_current_brush()
            self._load_brushes_refresh()
            self._set_message(f"Imported {len(borders)} border definition(s) from XML " f"({changed} rule(s) changed).")
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Import Failed",
                f"Failed to import borders.xml:\n{exc}",
            )

    def _export_borders_xml(self) -> None:
        """Export current border definitions to legacy RME borders.xml format."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Legacy borders.xml",
            "borders.xml",
            "XML files (*.xml);;All files (*)",
        )
        if not path:
            return

        try:
            from py_rme_canary.logic_layer.borders.borders_xml_io import export_borders_xml

            count = export_borders_xml(self.brush_manager, path)
            self._set_message(f"Exported {count} border definition(s) to {path}.")
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export borders.xml:\n{exc}",
            )

    def _load_brushes_refresh(self) -> None:
        """Refresh the brush list after an import operation."""
        current_row = self.brush_list.currentRow()
        self.brush_list.clear()
        self._load_brushes()
        if current_row >= 0 and current_row < self.brush_list.count():
            self.brush_list.setCurrentRow(current_row)
