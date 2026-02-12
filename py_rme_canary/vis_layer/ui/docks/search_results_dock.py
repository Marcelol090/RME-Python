"""Modern Search Results Dock.

Provides a persistent list of search results with:
- Clickable items to jump to location
- Column sorting
- Filter/highlight capabilities
- Export results to file

Reference:
    - GAP_ANALYSIS.md: P1 - Search Results Dock

Layer: vis_layer (PyQt6 UI)
"""

from __future__ import annotations

import contextlib

import csv
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SearchResult:
    """Single search result entry.

    Attributes:
        x: Tile X coordinate.
        y: Tile Y coordinate.
        z: Floor level.
        item_id: Item ID that matched (if applicable).
        item_name: Display name of the item.
        match_type: Type of match (item, creature, spawn, etc).
        details: Additional match details.
        timestamp: When this result was found.
    """

    x: int
    y: int
    z: int
    item_id: int = 0
    item_name: str = ""
    match_type: str = "item"
    details: str = ""
    timestamp: float = 0.0


@dataclass
class SearchResultSet:
    """Collection of search results from a single query.

    Attributes:
        query: Original search query.
        results: List of SearchResult entries.
        search_time: When the search was performed.
        scope: Search scope (all, selection, floor).
    """

    query: str = ""
    results: list[SearchResult] = field(default_factory=list)
    search_time: datetime = field(default_factory=datetime.now)
    scope: str = "all"

    @property
    def count(self) -> int:
        return len(self.results)


class SearchResultsTableWidget(QTableWidget):
    """Table widget for displaying search results."""

    # Signal: (x, y, z) when user double-clicks
    jump_to_position = pyqtSignal(int, int, int)

    # Columns
    COLUMNS = [
        ("Position", 100),
        ("Floor", 50),
        ("Type", 80),
        ("Name/ID", 150),
        ("Details", 200),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_table()
        self._results: list[SearchResult] = []

    def _setup_table(self) -> None:
        """Configure table appearance."""
        self.setColumnCount(len(self.COLUMNS))
        self.setHorizontalHeaderLabels([c[0] for c in self.COLUMNS])

        # Column widths
        header = self.horizontalHeader()
        for i, (_, width) in enumerate(self.COLUMNS):
            header.setSectionResizeMode(
                i, QHeaderView.ResizeMode.Interactive if i < len(self.COLUMNS) - 1 else QHeaderView.ResizeMode.Stretch
            )
            self.setColumnWidth(i, width)

        # Appearance
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSortingEnabled(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Double-click to jump
        self.doubleClicked.connect(self._on_double_click)

        # Styling
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.setStyleSheet(
            f"""
            QTableWidget {{
                background: {c["surface"]["primary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["sm"]}px;
                gridline-color: {c["surface"]["secondary"]};
            }}
            QTableWidget::item {{
                color: {c["text"]["primary"]};
                padding: 4px 8px;
            }}
            QTableWidget::item:selected {{
                background: {c["brand"]["primary"]};
            }}
            QTableWidget::item:hover {{
                background: {c["surface"]["secondary"]};
            }}
            QHeaderView::section {{
                background: {c["surface"]["secondary"]};
                color: {c["text"]["primary"]};
                padding: 6px;
                border: none;
                border-right: 1px solid {c["border"]["default"]};
                border-bottom: 1px solid {c["border"]["default"]};
            }}
        """
        )

    def set_results(self, results: list[SearchResult]) -> None:
        """Populate table with search results."""
        self._results = results
        self.setRowCount(0)  # Clear
        self.setSortingEnabled(False)  # Disable during population

        for result in results:
            row = self.rowCount()
            self.insertRow(row)

            # Position (sortable by x*1000000 + y)
            pos_item = QTableWidgetItem(f"{result.x}, {result.y}")
            pos_item.setData(Qt.ItemDataRole.UserRole, result.x * 1000000 + result.y)
            pos_item.setData(Qt.ItemDataRole.UserRole + 1, result)  # Store result
            self.setItem(row, 0, pos_item)

            # Floor
            floor_item = QTableWidgetItem(str(result.z))
            floor_item.setData(Qt.ItemDataRole.UserRole, result.z)
            self.setItem(row, 1, floor_item)

            # Type
            type_item = QTableWidgetItem(result.match_type.capitalize())
            self.setItem(row, 2, type_item)

            # Name/ID
            name = result.item_name or str(result.item_id) if result.item_id else "-"
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, result.item_id)
            self.setItem(row, 3, name_item)

            # Details
            details_item = QTableWidgetItem(result.details)
            self.setItem(row, 4, details_item)

        self.setSortingEnabled(True)

    def filter_results(self, text: str) -> None:
        """Show only rows matching filter text."""
        text = text.lower()
        for row in range(self.rowCount()):
            match = False
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.setRowHidden(row, not match)

    def get_selected_results(self) -> list[SearchResult]:
        """Get list of currently selected results."""
        selected: list[SearchResult] = []
        for index in self.selectedIndexes():
            if index.column() == 0:  # Only process once per row
                item = self.item(index.row(), 0)
                if item:
                    result = item.data(Qt.ItemDataRole.UserRole + 1)
                    if isinstance(result, SearchResult):
                        selected.append(result)
        return selected

    def _on_double_click(self, index) -> None:
        """Handle double-click to jump to position."""
        item = self.item(index.row(), 0)
        if item:
            result = item.data(Qt.ItemDataRole.UserRole + 1)
            if isinstance(result, SearchResult):
                self.jump_to_position.emit(result.x, result.y, result.z)

    def _show_context_menu(self, pos) -> None:
        """Show context menu for selected results."""
        menu = QMenu(self)

        jump_action = menu.addAction("Jump to Location")
        copy_pos_action = menu.addAction("Copy Position")
        menu.addSeparator()
        select_all_action = menu.addAction("Select All on Map")

        action = menu.exec(self.viewport().mapToGlobal(pos))

        selected = self.get_selected_results()
        if not selected:
            return

        if action == jump_action and selected:
            first = selected[0]
            self.jump_to_position.emit(first.x, first.y, first.z)
        elif action == copy_pos_action:
            text = "\n".join(f"{r.x}, {r.y}, {r.z}" for r in selected)
            QApplication.clipboard().setText(text)
        elif action == select_all_action:
            pass  # TODO: implement select-all-on-map


class SearchResultsDock(QDockWidget):
    """Dock widget for persistent search results.

    Provides:
    - Searchable/sortable results table
    - Click-to-jump functionality
    - Export to CSV
    - Result history

    Signals:
        jump_requested: Emitted when user wants to jump (x, y, z)
        selection_requested: Emitted when user wants to select results
    """

    jump_requested = pyqtSignal(int, int, int)
    selection_requested = pyqtSignal(list)  # list of (x, y, z)

    def __init__(self, editor: QtMapEditor | None = None, parent: QWidget | None = None) -> None:
        super().__init__("Search Results", parent)
        self.editor = editor

        self._result_sets: list[SearchResultSet] = []
        self._current_set: SearchResultSet | None = None

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        # History dropdown
        self.history_combo = QComboBox()
        self.history_combo.setMinimumWidth(200)
        self.history_combo.setPlaceholderText("Search history...")
        self.history_combo.currentIndexChanged.connect(self._on_history_changed)
        toolbar.addWidget(self.history_combo)

        toolbar.addStretch()

        # Filter input
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter results...")
        self.filter_input.setMaximumWidth(200)
        self.filter_input.textChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.filter_input)

        # Export button
        self.export_btn = QPushButton("Export...")
        self.export_btn.clicked.connect(self._export_results)
        toolbar.addWidget(self.export_btn)

        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_results)
        toolbar.addWidget(self.clear_btn)

        layout.addLayout(toolbar)

        # Results table
        self.table = SearchResultsTableWidget()
        self.table.jump_to_position.connect(self._on_jump_requested)
        layout.addWidget(self.table)

        # Status bar
        self.status_label = QLabel("No results")
        tm = get_theme_manager()
        c_ = tm.tokens["color"]
        self.status_label.setStyleSheet(f"color: {c_['text']['tertiary']}; font-size: 11px;")
        layout.addWidget(self.status_label)

        self.setWidget(container)

    def _apply_style(self) -> None:
        """Apply themed styling using design tokens."""
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.setStyleSheet(
            f"""
            QDockWidget {{
                background: {c["surface"]["primary"]};
                color: {c["text"]["primary"]};
            }}
            QComboBox {{
                background: {c["surface"]["secondary"]};
                color: {c["text"]["primary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["sm"]}px;
                padding: 4px 8px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QLineEdit {{
                background: {c["surface"]["secondary"]};
                color: {c["text"]["primary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["sm"]}px;
                padding: 4px 8px;
            }}
            QPushButton {{
                background: {c["surface"]["tertiary"]};
                color: {c["text"]["primary"]};
                border: none;
                border-radius: {r["sm"]}px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background: {c["brand"]["primary"]};
            }}
        """
        )

    def add_results(self, results: list[SearchResult], query: str = "", scope: str = "all") -> None:
        """Add a new result set.

        Args:
            results: List of SearchResult objects.
            query: The search query that produced these results.
            scope: Search scope (all, selection, floor).
        """
        result_set = SearchResultSet(
            query=query,
            results=results,
            scope=scope,
        )

        self._result_sets.insert(0, result_set)

        # Limit history
        if len(self._result_sets) > 20:
            self._result_sets = self._result_sets[:20]

        # Update history dropdown
        self._update_history_combo()

        # Show new results
        self.history_combo.setCurrentIndex(0)
        self._show_result_set(result_set)

    def _show_result_set(self, result_set: SearchResultSet) -> None:
        """Display a result set in the table."""
        self._current_set = result_set
        self.table.set_results(result_set.results)
        self._update_status()

    def _update_history_combo(self) -> None:
        """Update history dropdown with result sets."""
        self.history_combo.blockSignals(True)
        self.history_combo.clear()

        for result_set in self._result_sets:
            time_str = result_set.search_time.strftime("%H:%M:%S")
            label = f"[{time_str}] {result_set.query} ({result_set.count} results)"
            self.history_combo.addItem(label)

        self.history_combo.blockSignals(False)

    def _update_status(self) -> None:
        """Update status label."""
        if self._current_set is None:
            self.status_label.setText("No results")
        else:
            visible = sum(1 for row in range(self.table.rowCount()) if not self.table.isRowHidden(row))
            total = self._current_set.count

            if visible == total:
                self.status_label.setText(f"{total} result(s)")
            else:
                self.status_label.setText(f"Showing {visible} of {total} result(s)")

    def _on_history_changed(self, index: int) -> None:
        """Handle history dropdown selection."""
        if 0 <= index < len(self._result_sets):
            self._show_result_set(self._result_sets[index])

    def _on_filter_changed(self, text: str) -> None:
        """Handle filter input changes."""
        self.table.filter_results(text)
        self._update_status()

    def _on_jump_requested(self, x: int, y: int, z: int) -> None:
        """Handle jump request from table."""
        self.jump_requested.emit(x, y, z)

        # Also try to navigate editor directly
        if self.editor is not None:
            with contextlib.suppress(Exception):
                self.editor.center_on_position(x, y, z)

    def _export_results(self) -> None:
        """Export current results to CSV file."""
        if self._current_set is None or not self._current_set.results:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Search Results",
            f"search_results_{datetime.now():%Y%m%d_%H%M%S}.csv",
            "CSV Files (*.csv);;All Files (*)",
        )

        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Header
                writer.writerow(["X", "Y", "Z", "Type", "Item ID", "Name", "Details"])

                # Data
                for result in self._current_set.results:
                    writer.writerow(
                        [
                            result.x,
                            result.y,
                            result.z,
                            result.match_type,
                            result.item_id,
                            result.item_name,
                            result.details,
                        ]
                    )

            logger.info("Exported %d results to %s", self._current_set.count, path)

        except Exception as e:
            logger.error("Export failed: %s", e)

    def _clear_results(self) -> None:
        """Clear current result set."""
        if self._current_set:
            self._result_sets.remove(self._current_set)
            self._current_set = None
            self.table.setRowCount(0)
            self._update_history_combo()
            self._update_status()

    def select_all_results(self) -> None:
        """Select all current results on the map."""
        if self._current_set is None:
            return

        positions = [(r.x, r.y, r.z) for r in self._current_set.results]
        self.selection_requested.emit(positions)


def create_search_results_dock(editor: QtMapEditor) -> SearchResultsDock:
    """Factory function to create the search results dock.

    Args:
        editor: The QtMapEditor instance.

    Returns:
        Configured SearchResultsDock.
    """
    dock = SearchResultsDock(editor)
    dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea)
    return dock
