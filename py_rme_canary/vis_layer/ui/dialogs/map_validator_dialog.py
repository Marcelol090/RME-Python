"""Map Validator Dialog.

UI dialog for running map validation checks and displaying results.
Uses the core/io/map_validator.py for validation logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


class ValidationWorker(QThread):
    """Worker thread for running validation."""

    progress = pyqtSignal(int, str)  # progress %, message
    finished = pyqtSignal(list)  # list of issues

    def __init__(self, map_data: GameMap | None) -> None:
        super().__init__()
        self._map = map_data

    @staticmethod
    def _format_location(context: dict[str, object]) -> str:
        """Format validator context into a readable location string."""
        if not context:
            return "N/A"

        position = context.get("position")
        if isinstance(position, tuple) and len(position) == 3:
            return f"{int(position[0])}, {int(position[1])}, {int(position[2])}"

        sample = context.get("sample")
        if isinstance(sample, list) and sample:
            first = sample[0]
            if isinstance(first, tuple) and len(first) == 3:
                return f"{int(first[0])}, {int(first[1])}, {int(first[2])}"

        ordered_keys = [
            "house_id",
            "town_id",
            "zone_id",
            "count",
            "radius",
            "width",
            "height",
            "name",
        ]
        parts: list[str] = []
        for key in ordered_keys:
            if key in context:
                parts.append(f"{key}={context[key]}")
        if parts:
            return ", ".join(parts)

        return ", ".join(f"{k}={v}" for k, v in list(context.items())[:3]) or "N/A"

    def _collect_item_id_issues(self) -> list[dict[str, str]]:
        """Collect warnings for invalid/unknown item ids across the map."""
        if self._map is None:
            return []

        invalid_count = 0
        samples: list[str] = []

        for tile in self._map.iter_tiles():
            stack = []
            if tile.ground is not None:
                stack.append(tile.ground)
            stack.extend(list(tile.items or []))

            while stack:
                item = stack.pop()
                item_id = int(getattr(item, "id", 0))
                raw_unknown = getattr(item, "raw_unknown_id", None)
                if item_id <= 0 or raw_unknown is not None:
                    invalid_count += 1
                    if len(samples) < 5:
                        suffix = f" (raw={int(raw_unknown)})" if raw_unknown is not None else ""
                        samples.append(f"{int(tile.x)}, {int(tile.y)}, {int(tile.z)} -> id={item_id}{suffix}")

                children = tuple(getattr(item, "items", ()) or ())
                if children:
                    stack.extend(children)

        if invalid_count == 0:
            return []

        location = "; ".join(samples) if samples else "N/A"
        return [
            {
                "type": "warning",
                "message": f"Found {invalid_count} item(s) with invalid or unknown IDs",
                "location": location,
            }
        ]

    def run(self) -> None:
        """Run validation checks."""
        issues: list[dict[str, str]] = []

        if self._map is None:
            self.finished.emit([{"type": "error", "message": "No map loaded", "location": "N/A"}])
            return

        try:
            from py_rme_canary.core.io.map_validator import validate_game_map

            self.progress.emit(10, "Checking map dimensions and bounds...")
            result = validate_game_map(self._map)

            base_issues: list[dict[str, str]] = []
            spawn_issues: list[dict[str, str]] = []
            house_issues: list[dict[str, str]] = []
            waypoint_issues: list[dict[str, str]] = []
            other_issues: list[dict[str, str]] = []

            for issue in result.issues:
                issue_data = {
                    "type": str(issue.severity),
                    "message": str(issue.message),
                    "location": self._format_location(issue.context),
                }

                code = str(issue.code or "").upper()
                if "SPAWN" in code:
                    spawn_issues.append(issue_data)
                elif code.startswith("HOUSE_"):
                    house_issues.append(issue_data)
                elif code.startswith("WAYPOINT_"):
                    waypoint_issues.append(issue_data)
                elif code.startswith(("MAP_", "TILE_", "TOWN_", "ZONE_")):
                    base_issues.append(issue_data)
                else:
                    other_issues.append(issue_data)

            issues.extend(base_issues)

            self.progress.emit(30, "Checking spawn points...")
            issues.extend(spawn_issues)

            self.progress.emit(50, "Checking house tiles...")
            issues.extend(house_issues)

            self.progress.emit(70, "Checking waypoints...")
            issues.extend(waypoint_issues)

            self.progress.emit(90, "Checking item IDs...")
            issues.extend(other_issues)
            issues.extend(self._collect_item_id_issues())

        except Exception as exc:
            issues.append(
                {
                    "type": "error",
                    "message": "Validation failed unexpectedly",
                    "location": str(exc),
                }
            )

        self.progress.emit(100, "Validation complete")
        self.finished.emit(issues)


class MapValidatorDialog(ModernDialog):
    """Dialog for map validation results.

    Usage:
        dialog = MapValidatorDialog(parent, map_data)
        dialog.exec()
    """

    def __init__(self, parent: QWidget | None = None, map_data: GameMap | None = None) -> None:
        super().__init__(parent, title="Map Validator")
        self._map = map_data
        self._worker: ValidationWorker | None = None

        self.setModal(True)
        self.resize(600, 400)

        self._populate_ui()

    def _populate_ui(self) -> None:
        """Initialize UI components."""
        layout = self.content_layout

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setTextVisible(True)
        self._progress.setFormat("%p% - %v")
        layout.addWidget(self._progress)

        # Status label
        self._status = QLabel("Click 'Validate' to start...")
        self._status.setStyleSheet("color: #9CA3AF;")
        layout.addWidget(self._status)

        # Results table
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Type", "Message", "Location"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)

        # Summary
        self._summary = QLabel("")
        self._summary.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        layout.addWidget(self._summary)

        # Buttons
        self.footer.setVisible(True)

        self._validate_btn = QPushButton("Validate")
        self._validate_btn.clicked.connect(self._start_validation)
        self.footer_layout.addWidget(self._validate_btn)

        self.add_spacer_to_footer()

        self.add_button("Close", callback=self.reject)

    def _start_validation(self) -> None:
        """Start the validation process."""
        self._validate_btn.setEnabled(False)
        self._table.setRowCount(0)
        self._progress.setValue(0)
        self._status.setText("Validating...")

        self._worker = ValidationWorker(self._map)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, percent: int, message: str) -> None:
        """Handle progress update."""
        self._progress.setValue(percent)
        self._status.setText(message)

    def _on_finished(self, issues: list[dict[str, str]]) -> None:
        """Handle validation complete."""
        self._validate_btn.setEnabled(True)

        # Populate table
        self._table.setRowCount(len(issues))

        errors = 0
        warnings = 0

        for row, issue in enumerate(issues):
            issue_type = issue.get("type", "info")

            # Type cell with color coding
            type_item = QTableWidgetItem(issue_type.upper())
            if issue_type == "error":
                type_item.setForeground(Qt.GlobalColor.red)
                errors += 1
            elif issue_type == "warning":
                type_item.setForeground(Qt.GlobalColor.yellow)
                warnings += 1
            else:
                type_item.setForeground(Qt.GlobalColor.cyan)
            self._table.setItem(row, 0, type_item)

            # Message
            self._table.setItem(row, 1, QTableWidgetItem(issue.get("message", "")))

            # Location
            self._table.setItem(row, 2, QTableWidgetItem(issue.get("location", "")))

        # Summary
        if not issues:
            self._summary.setText("No issues found. Map is valid.")
            self._summary.setStyleSheet("color: #22C55E; font-size: 11px;")
        else:
            self._summary.setText(f"Found {errors} error(s), {warnings} warning(s)")
            self._summary.setStyleSheet(
                "color: #EF4444; font-size: 11px;" if errors else "color: #F59E0B; font-size: 11px;"
            )

        self._status.setText("Validation complete")
