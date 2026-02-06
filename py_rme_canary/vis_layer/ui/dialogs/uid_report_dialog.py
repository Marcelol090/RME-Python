"""UID Report Dialog for RME.

Displays duplicate UID warnings with navigation to conflicts.

Layer: vis_layer (uses PyQt6)
"""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class UIDReportDialog(QDialog):
    """Dialog showing duplicate UID conflicts."""

    def __init__(
        self,
        parent: QWidget | None = None,
        session: Any = None,
    ) -> None:
        super().__init__(parent)
        self._session = session
        self._conflicts: list[Any] = []

        self.setWindowTitle("Duplicate UID Report")
        self.setMinimumSize(600, 400)
        self.setModal(False)  # Allow interaction with main window

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Status label
        self._status_label = QLabel("Click 'Scan' to check for duplicate UIDs")
        layout.addWidget(self._status_label)

        # Results table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["UID", "Count", "Item IDs", "Positions"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._table)

        # Buttons
        button_layout = QHBoxLayout()

        self._scan_btn = QPushButton("Scan Map")
        self._scan_btn.clicked.connect(self._on_scan)
        button_layout.addWidget(self._scan_btn)

        self._goto_btn = QPushButton("Go To Selected")
        self._goto_btn.clicked.connect(self._on_goto)
        button_layout.addWidget(self._goto_btn)

        button_layout.addStretch()

        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self._close_btn)

        layout.addLayout(button_layout)

    def _on_scan(self) -> None:
        """Run UID validation scan."""
        from py_rme_canary.logic_layer.uid_validator import get_uid_validator

        if not self._session:
            QMessageBox.warning(self, "No Session", "No map is currently loaded.")
            return

        game_map = getattr(self._session, "game_map", None)
        if game_map is None:
            game_map = getattr(self._session, "map", None)

        if game_map is None:
            QMessageBox.warning(self, "No Map", "Could not access map data.")
            return

        # Run scan
        validator = get_uid_validator()
        result = validator.scan(game_map)

        self._conflicts = result.conflicts

        # Update UI
        self._table.setRowCount(0)

        if result.has_duplicates:
            self._status_label.setText(
                f"Found {result.duplicate_count} duplicate UID(s) ({result.total_items_scanned} items scanned)"
            )
            self._status_label.setStyleSheet("color: #e57373; font-weight: bold;")

            for conflict in result.conflicts:
                row = self._table.rowCount()
                self._table.insertRow(row)

                self._table.setItem(row, 0, QTableWidgetItem(str(conflict.unique_id)))
                self._table.setItem(row, 1, QTableWidgetItem(str(conflict.count)))

                item_ids = ", ".join(str(i) for i in conflict.item_ids[:3])
                if len(conflict.item_ids) > 3:
                    item_ids += f" (+{len(conflict.item_ids) - 3})"
                self._table.setItem(row, 2, QTableWidgetItem(item_ids))

                pos_str = ", ".join(f"({x},{y},{z})" for x, y, z in conflict.positions[:2])
                if len(conflict.positions) > 2:
                    pos_str += f" (+{len(conflict.positions) - 2})"
                self._table.setItem(row, 3, QTableWidgetItem(pos_str))
        else:
            self._status_label.setText(f"No duplicate UIDs found ({result.total_items_scanned} items scanned)")
            self._status_label.setStyleSheet("color: #81c784; font-weight: bold;")

    def _on_goto(self) -> None:
        """Navigate to selected conflict position."""
        row = self._table.currentRow()
        if row < 0 or row >= len(self._conflicts):
            return

        conflict = self._conflicts[row]
        if conflict.positions:
            x, y, z = conflict.positions[0]
            self._go_to_position(x, y, z)

    def _on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        """Handle double-click on table item."""
        self._on_goto()

    def _go_to_position(self, x: int, y: int, z: int) -> None:
        """Go to the specified position on the map."""
        if not self._session:
            return

        if hasattr(self._session, "go_to_position"):
            self._session.go_to_position(x, y, z)
        elif hasattr(self._session, "center_on"):
            self._session.center_on(x, y, z)
        elif hasattr(self._session, "viewport"):
            viewport = self._session.viewport
            if hasattr(viewport, "center_on"):
                viewport.center_on(x, y)
            elif hasattr(viewport, "camera_pos"):
                viewport.camera_pos = (x, y)
