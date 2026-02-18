"""Item Find and Replace Dialog.

Advanced search and replace for items on the map.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog
from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


class ItemFindReplaceDialog(ModernDialog):
    """Dialog for finding and replacing items.

    Features:
    - Find items by ID or name
    - Replace with different item
    - Scope: whole map, selection, current floor
    - Preview matches before replacing
    """

    def __init__(self, game_map: GameMap | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent, title="Find & Replace Items")

        self._game_map = game_map
        self._match_count = 0

        self.setMinimumSize(450, 400)
        self.setModal(True)

        self._setup_content()
        self._apply_style()

    def _setup_content(self) -> None:
        """Initialize UI."""
        # Use content_layout from ModernDialog
        layout = self.content_layout
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Find section
        find_group = QGroupBox("Find")
        find_layout = QFormLayout(find_group)

        find_row = QHBoxLayout()
        self.find_id = QSpinBox()
        self.find_id.setRange(0, 65535)
        self.find_id.setSpecialValueText("Any")
        find_row.addWidget(self.find_id)

        self.find_name = QLineEdit()
        self.find_name.setPlaceholderText("Or search by name...")
        find_row.addWidget(self.find_name)

        find_layout.addRow("Item ID:", find_row)

        layout.addWidget(find_group)

        # Replace section
        replace_group = QGroupBox("Replace With")
        replace_layout = QFormLayout(replace_group)

        self.replace_id = QSpinBox()
        self.replace_id.setRange(0, 65535)
        replace_layout.addRow("Item ID:", self.replace_id)

        self.delete_mode = QCheckBox("Delete instead of replace")
        self.delete_mode.stateChanged.connect(self._on_delete_mode_changed)
        replace_layout.addRow(self.delete_mode)

        layout.addWidget(replace_group)

        # Scope section
        scope_group = QGroupBox("Search Scope")
        scope_layout = QVBoxLayout(scope_group)

        self.scope_all = QRadioButton("Entire map")
        self.scope_all.setChecked(True)
        scope_layout.addWidget(self.scope_all)

        self.scope_selection = QRadioButton("Selection only")
        scope_layout.addWidget(self.scope_selection)

        self.scope_floor = QRadioButton("Current floor only")
        scope_layout.addWidget(self.scope_floor)

        layout.addWidget(scope_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        self.match_ground = QCheckBox("Include ground tiles")
        self.match_ground.setChecked(True)
        options_layout.addWidget(self.match_ground)

        self.match_items = QCheckBox("Include items on tiles")
        self.match_items.setChecked(True)
        options_layout.addWidget(self.match_items)

        layout.addWidget(options_group)

        # Results
        self.results_label = QLabel("")
        self.results_label.setObjectName("ResultsLabel")
        layout.addWidget(self.results_label)

        # Progress
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Buttons (Footer)
        self.add_spacer_to_footer()

        self.btn_find = self.add_button("Find All", callback=self._do_find, role="primary")

        self.btn_replace_all = self.add_button("Replace All", callback=self._do_replace_all, role="secondary")
        self.btn_replace_all.setEnabled(False)

        # Close button is handled by header "x" but usually modern dialogs have a close or cancel in footer?
        # ModernDialog has a close button in the header. We can add a "Close" button to the footer if desired.
        self.add_button("Close", callback=self.accept, role="secondary")


    def _apply_style(self) -> None:
        """Apply modern styling."""
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        # Note: We apply styles to specific widgets because ModernDialog handles the base window style.
        # But we can still style children.

        self.setStyleSheet(f"""
            QGroupBox {{
                background: {c["surface"]["secondary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["md"]}px;
                margin-top: 12px;
                padding-top: 12px;
                color: {c["text"]["primary"]};
                font-weight: 600;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}

            QSpinBox, QLineEdit {{
                background: {c["surface"]["tertiary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["sm"]}px;
                padding: 6px;
                color: {c["text"]["primary"]};
            }}

            QSpinBox:focus, QLineEdit:focus {{
                border: 1px solid {c["brand"]["primary"]};
            }}

            QCheckBox, QRadioButton {{
                color: {c["text"]["primary"]};
            }}

            QLabel#ResultsLabel {{
                color: {c["text"]["secondary"]};
            }}

            QProgressBar {{
                background: {c["surface"]["tertiary"]};
                border: none;
                border-radius: {r["sm"]}px;
                height: 6px;
            }}

            QProgressBar::chunk {{
                background: {c["brand"]["primary"]};
                border-radius: {r["sm"]}px;
            }}

            QPushButton {{
                background: {c["surface"]["tertiary"]};
                color: {c["text"]["primary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["sm"]}px;
                padding: 6px 16px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: {c["state"]["hover"]};
                border-color: {c["brand"]["primary"]};
            }}

            QPushButton:disabled {{
                background: {c["surface"]["primary"]};
                color: {c["text"]["tertiary"]};
                border-color: {c["border"]["default"]};
            }}
        """)

    def _on_delete_mode_changed(self, state: int) -> None:
        """Handle delete mode toggle."""
        is_delete = state == Qt.CheckState.Checked.value
        self.replace_id.setEnabled(not is_delete)

    def _do_find(self) -> None:
        """Find all matching items."""
        if not self._game_map:
            self.results_label.setText("No map loaded")
            return

        find_id = self.find_id.value()
        if find_id == 0:
            self.results_label.setText("Please specify an item ID")
            return

        self.progress.show()
        self.progress.setMaximum(0)  # Indeterminate

        # Count matches
        count = 0
        tiles = getattr(self._game_map, "tiles", {}) or {}

        for _pos, tile in tiles.items():
            # Check scope
            if self.scope_floor.isChecked():
                # Would check against current floor
                pass
            elif self.scope_selection.isChecked():
                # Would check against selection
                pass

            # Check ground
            if self.match_ground.isChecked() and tile.ground and tile.ground.id == find_id:
                count += 1
                continue

            # Check items
            if self.match_items.isChecked():
                for item in tile.items:
                    if item.id == find_id:
                        count += 1
                        break

        self._match_count = count
        self.progress.hide()

        if count > 0:
            self.results_label.setText(f"Found {count} match{'es' if count != 1 else ''}")
            self.btn_replace_all.setEnabled(True)
        else:
            self.results_label.setText("No matches found")
            self.btn_replace_all.setEnabled(False)

    def _do_replace_all(self) -> None:
        """Replace all matching items."""
        if not self._game_map or self._match_count == 0:
            return

        find_id = self.find_id.value()
        replace_id = self.replace_id.value() if not self.delete_mode.isChecked() else None

        from PyQt6.QtWidgets import QMessageBox

        if self.delete_mode.isChecked():
            msg = f"Delete all {self._match_count} instances of item #{find_id}?"
        else:
            msg = f"Replace all {self._match_count} instances of item #{find_id} with #{replace_id}?"

        reply = QMessageBox.question(
            self, "Confirm Replace", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Perform replacement
        self.progress.show()
        self.progress.setMaximum(self._match_count)

        replaced = 0
        tiles = getattr(self._game_map, "tiles", {}) or {}

        for _pos, tile in tiles.items():
            # Check ground
            if self.match_ground.isChecked() and tile.ground and tile.ground.id == find_id:
                if self.delete_mode.isChecked():
                    tile.ground = None
                else:
                    tile.ground.id = replace_id
                replaced += 1
                self.progress.setValue(replaced)

            # Check items
            if self.match_items.isChecked():
                for item in tile.items:
                    if item.id == find_id:
                        if self.delete_mode.isChecked():
                            tile.items.remove(item)
                        else:
                            item.id = replace_id
                        replaced += 1
                        self.progress.setValue(replaced)
                        break

        self.progress.hide()
        self.results_label.setText(f"Replaced {replaced} item{'s' if replaced != 1 else ''}")
        self._match_count = 0
        self.btn_replace_all.setEnabled(False)
