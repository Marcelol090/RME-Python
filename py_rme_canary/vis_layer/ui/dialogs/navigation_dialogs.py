"""Go To Position Dialog - Navigate to specific coordinates.

Modern dialog for entering X, Y, Z coordinates with validation.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    pass


def _c() -> dict:
    return get_theme_manager().tokens["color"]


def _r() -> dict:
    return get_theme_manager().tokens.get("radius", {})


class GoToPositionDialog(QDialog):
    """Dialog for navigating to specific map coordinates.

    Features:
    - X, Y, Z input fields with validation
    - Recent positions list
    - Bookmark/save positions

    Signals:
        position_selected: Emits (x, y, z) tuple when user confirms
    """

    position_selected = pyqtSignal(int, int, int)

    def __init__(
        self,
        current_x: int = 0,
        current_y: int = 0,
        current_z: int = 7,
        map_width: int = 65535,
        map_height: int = 65535,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._current_x = current_x
        self._current_y = current_y
        self._current_z = current_z
        self._map_width = map_width
        self._map_height = map_height

        self.setWindowTitle("Go To Position")
        self.setMinimumWidth(300)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        c = _c()

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("Enter target position:")
        header.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {c['text']['primary']};")
        layout.addWidget(header)

        # Current position info
        current_label = QLabel(f"Current: ({self._current_x}, {self._current_y}, {self._current_z})")
        current_label.setStyleSheet(f"color: {c['text']['secondary']}; font-size: 12px;")
        layout.addWidget(current_label)

        # Coordinate inputs
        coords_layout = QHBoxLayout()
        coords_layout.setSpacing(12)

        # X
        x_container = QVBoxLayout()
        x_label = QLabel("X")
        x_label.setStyleSheet(f"color: {c['brand']['secondary']}; font-weight: 600;")
        x_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        x_container.addWidget(x_label)

        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, self._map_width)
        self.x_spin.setValue(self._current_x)
        self.x_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        x_container.addWidget(self.x_spin)
        coords_layout.addLayout(x_container)

        # Y
        y_container = QVBoxLayout()
        y_label = QLabel("Y")
        y_label.setStyleSheet(f"color: {c['brand']['active']}; font-weight: 600;")
        y_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        y_container.addWidget(y_label)

        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, self._map_height)
        self.y_spin.setValue(self._current_y)
        self.y_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        y_container.addWidget(self.y_spin)
        coords_layout.addLayout(y_container)

        # Z
        z_container = QVBoxLayout()
        z_label = QLabel("Z")
        z_label.setStyleSheet(f"color: {c['state']['success']}; font-weight: 600;")
        z_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        z_container.addWidget(z_label)

        self.z_spin = QSpinBox()
        self.z_spin.setRange(0, 15)
        self.z_spin.setValue(self._current_z)
        self.z_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        z_container.addWidget(self.z_spin)
        coords_layout.addLayout(z_container)

        layout.addLayout(coords_layout)

        # Quick actions
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(8)

        btn_center = QPushButton("Center")
        btn_center.setToolTip("Go to map center")
        btn_center.clicked.connect(self._goto_center)
        quick_layout.addWidget(btn_center)

        btn_origin = QPushButton("Origin")
        btn_origin.setToolTip("Go to (0, 0, 7)")
        btn_origin.clicked.connect(self._goto_origin)
        quick_layout.addWidget(btn_origin)

        btn_surface = QPushButton("Surface")
        btn_surface.setToolTip("Set Z to 7 (ground level)")
        btn_surface.clicked.connect(lambda: self.z_spin.setValue(7))
        quick_layout.addWidget(btn_surface)

        layout.addLayout(quick_layout)

        layout.addStretch()

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _apply_style(self) -> None:
        """Apply modern dark styling."""
        c = _c()
        r = _r()
        rad = r.get("md", 6)
        rad_lg = r.get("lg", 8)

        self.setStyleSheet(
            f"""
            QDialog {{
                background: {c['surface']['primary']};
            }}

            QSpinBox {{
                background: {c['surface']['secondary']};
                border: 2px solid {c['border']['default']};
                border-radius: {rad_lg}px;
                padding: 12px;
                color: {c['text']['primary']};
                font-size: 16px;
                font-weight: 600;
                min-width: 80px;
            }}

            QSpinBox:focus {{
                border-color: {c['brand']['secondary']};
            }}

            QSpinBox::up-button, QSpinBox::down-button {{
                width: 20px;
                background: {c['surface']['tertiary']};
                border: none;
            }}

            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background: {c['brand']['secondary']};
            }}

            QPushButton {{
                background: {c['surface']['tertiary']};
                color: {c['text']['primary']};
                border: 1px solid {c['border']['strong']};
                border-radius: {rad}px;
                padding: 8px 12px;
                font-size: 11px;
            }}

            QPushButton:hover {{
                background: {c['surface']['hover']};
                border-color: {c['brand']['secondary']};
            }}

            QDialogButtonBox QPushButton {{
                min-width: 80px;
            }}
        """
        )

    def _goto_center(self) -> None:
        """Set coordinates to map center."""
        self.x_spin.setValue(self._map_width // 2)
        self.y_spin.setValue(self._map_height // 2)

    def _goto_origin(self) -> None:
        """Set coordinates to origin."""
        self.x_spin.setValue(0)
        self.y_spin.setValue(0)
        self.z_spin.setValue(7)

    def _on_accept(self) -> None:
        """Handle dialog accept."""
        x = self.x_spin.value()
        y = self.y_spin.value()
        z = self.z_spin.value()
        self.position_selected.emit(x, y, z)
        self.accept()

    def get_position(self) -> tuple[int, int, int]:
        """Get the entered position.

        Returns:
            Tuple of (x, y, z) coordinates
        """
        return (self.x_spin.value(), self.y_spin.value(), self.z_spin.value())


class FindItemDialog(QDialog):
    """Enhanced Find Item dialog with modern styling.

    Features:
    - Search by item ID or name
    - Filter by item properties
    - Results list with navigation
    """

    item_selected = pyqtSignal(int, int, int)  # x, y, z of found item

    def __init__(self, parent: QWidget | None = None, on_search: Callable[[int], list] | None = None) -> None:
        super().__init__(parent)

        self._on_search = on_search
        self._results: list = []

        self.setWindowTitle("Find Item")
        self.setMinimumSize(400, 300)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        c = _c()

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Search input
        search_layout = QHBoxLayout()

        search_label = QLabel("Item ID:")
        search_label.setStyleSheet(f"color: {c['text']['primary']}; font-weight: 500;")
        search_layout.addWidget(search_label)

        self.search_spin = QSpinBox()
        self.search_spin.setRange(0, 65535)
        self.search_spin.setMinimumWidth(120)
        search_layout.addWidget(self.search_spin)

        self.btn_search = QPushButton("Search")
        self.btn_search.clicked.connect(self._do_search)
        search_layout.addWidget(self.btn_search)

        search_layout.addStretch()

        layout.addLayout(search_layout)

        # Results
        results_label = QLabel("Results:")
        results_label.setStyleSheet(f"color: {c['text']['secondary']}; font-size: 12px;")
        layout.addWidget(results_label)

        from PyQt6.QtWidgets import QListWidget

        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self._on_result_selected)
        layout.addWidget(self.results_list)

        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {c['text']['disabled']}; font-size: 11px;")
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.btn_goto = QPushButton("Go To")
        self.btn_goto.setEnabled(False)
        self.btn_goto.clicked.connect(self._goto_selected)
        button_layout.addWidget(self.btn_goto)

        button_layout.addStretch()

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        button_layout.addWidget(btn_close)

        layout.addLayout(button_layout)

    def _apply_style(self) -> None:
        """Apply modern dark styling."""
        c = _c()
        r = _r()
        rad = r.get("md", 6)
        rad_lg = r.get("lg", 8)
        rad_sm = r.get("sm", 4)

        self.setStyleSheet(
            f"""
            QDialog {{
                background: {c['surface']['primary']};
            }}

            QSpinBox {{
                background: {c['surface']['secondary']};
                border: 1px solid {c['border']['default']};
                border-radius: {rad}px;
                padding: 8px;
                color: {c['text']['primary']};
            }}

            QSpinBox:focus {{
                border-color: {c['brand']['secondary']};
            }}

            QPushButton {{
                background: {c['brand']['secondary']};
                color: white;
                border: none;
                border-radius: {rad}px;
                padding: 8px 16px;
                font-weight: 500;
            }}

            QPushButton:hover {{
                background: {c['brand']['hover']};
            }}

            QPushButton:disabled {{
                background: {c['surface']['tertiary']};
                color: {c['text']['disabled']};
            }}

            QListWidget {{
                background: {c['surface']['secondary']};
                border: 1px solid {c['border']['default']};
                border-radius: {rad_lg}px;
                color: {c['text']['primary']};
            }}

            QListWidget::item {{
                padding: 8px;
                border-radius: {rad_sm}px;
            }}

            QListWidget::item:hover {{
                background: {c['surface']['tertiary']};
            }}

            QListWidget::item:selected {{
                background: {c['brand']['secondary']};
            }}
        """
        )

    def _do_search(self) -> None:
        """Execute search."""
        item_id = self.search_spin.value()

        self.results_list.clear()
        self._results.clear()

        if self._on_search:
            try:
                results = self._on_search(item_id)
                self._results = results or []

                for i, (x, y, z) in enumerate(self._results[:100]):
                    from PyQt6.QtWidgets import QListWidgetItem

                    text = f"#{i + 1}: ({x}, {y}, {z})"
                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, (x, y, z))
                    self.results_list.addItem(item)

                count = len(self._results)
                if count > 100:
                    self.status_label.setText(f"Found {count} results (showing first 100)")
                else:
                    self.status_label.setText(f"Found {count} results")

            except Exception as e:
                self.status_label.setText(f"Error: {e}")
        else:
            self.status_label.setText("Search not available")

        self.btn_goto.setEnabled(len(self._results) > 0)

    def _on_result_selected(self, item: object) -> None:
        """Handle result double-click."""
        pos = item.data(Qt.ItemDataRole.UserRole)
        if pos:
            x, y, z = pos
            self.item_selected.emit(x, y, z)

    def _goto_selected(self) -> None:
        """Go to selected result."""
        items = self.results_list.selectedItems()
        if items:
            pos = items[0].data(Qt.ItemDataRole.UserRole)
            if pos:
                x, y, z = pos
                self.item_selected.emit(x, y, z)
