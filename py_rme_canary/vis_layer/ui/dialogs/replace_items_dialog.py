"""Replace Items Dialog for RME.

Provides UI for replacing items on the map with various scope options.

Layer: vis_layer (uses PyQt6)
"""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class ReplaceItemsDialog(QDialog):
    """Dialog for replacing items on the map."""

    def __init__(
        self,
        parent: QWidget | None = None,
        session: Any = None,
    ) -> None:
        super().__init__(parent)
        self._session = session

        self.setWindowTitle("Replace Items")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Source/Target group
        items_group = QGroupBox("Item IDs")
        items_layout = QVBoxLayout(items_group)

        # Source ID
        source_row = QHBoxLayout()
        source_row.addWidget(QLabel("Find Item ID:"))
        self._source_spin = QSpinBox()
        self._source_spin.setRange(1, 65535)
        self._source_spin.setValue(100)
        source_row.addWidget(self._source_spin)
        source_row.addStretch()
        items_layout.addLayout(source_row)

        # Target ID
        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Replace With ID:"))
        self._target_spin = QSpinBox()
        self._target_spin.setRange(1, 65535)
        self._target_spin.setValue(100)
        target_row.addWidget(self._target_spin)
        target_row.addStretch()
        items_layout.addLayout(target_row)

        layout.addWidget(items_group)

        # Scope group
        scope_group = QGroupBox("Replace Scope")
        scope_layout = QVBoxLayout(scope_group)

        self._scope_combo = QComboBox()
        self._scope_combo.addItem("Visible Screen Only", "visible")
        self._scope_combo.addItem("Current Selection", "selection")
        self._scope_combo.addItem("Entire Map", "entire_map")
        scope_layout.addWidget(self._scope_combo)

        layout.addWidget(scope_group)

        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        # Limit
        limit_row = QHBoxLayout()
        limit_row.addWidget(QLabel("Max Replacements:"))
        self._limit_spin = QSpinBox()
        self._limit_spin.setRange(1, 100000)
        self._limit_spin.setValue(500)
        limit_row.addWidget(self._limit_spin)
        limit_row.addStretch()
        options_layout.addLayout(limit_row)

        self._selection_only_cb = QCheckBox("Selection only (if available)")
        options_layout.addWidget(self._selection_only_cb)

        layout.addWidget(options_group)

        # Result label
        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

        # Buttons
        button_layout = QHBoxLayout()

        self._replace_btn = QPushButton("Replace")
        self._replace_btn.clicked.connect(self._on_replace)
        button_layout.addWidget(self._replace_btn)

        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._close_btn)

        layout.addLayout(button_layout)

    def _on_replace(self) -> None:
        """Execute replacement."""
        from py_rme_canary.logic_layer.replace_items import (
            replace_items_in_map,
        )

        if not self._session:
            QMessageBox.warning(self, "No Session", "No map is currently loaded.")
            return

        source_id = int(self._source_spin.value())
        target_id = int(self._target_spin.value())
        limit = int(self._limit_spin.value())
        selection_only = self._selection_only_cb.isChecked()

        if source_id == target_id:
            QMessageBox.warning(self, "Same ID", "Source and target IDs are the same.")
            return

        try:
            # Get game map
            game_map = getattr(self._session, "game_map", None)
            if game_map is None:
                game_map = getattr(self._session, "map", None)

            if game_map is None:
                QMessageBox.warning(self, "No Map", "Could not access map data.")
                return

            # Get selection tiles if needed
            selection_tiles = None
            if selection_only and hasattr(self._session, "selection"):
                selection = getattr(self._session, "selection", None)
                if selection:
                    selection_tiles = getattr(selection, "tiles_set", None)
                    if selection_tiles is None:
                        selection_tiles = {(t.x, t.y, t.z) for t in getattr(selection, "tiles", [])}

            # Execute replacement
            changed_tiles, result = replace_items_in_map(
                game_map,
                from_id=source_id,
                to_id=target_id,
                limit=limit,
                selection_only=selection_only,
                selection_tiles=selection_tiles,
            )

            # Apply changes to map
            for key, tile in changed_tiles.items():
                if hasattr(game_map, "set_tile"):
                    game_map.set_tile(tile)
                elif hasattr(game_map, "tiles"):
                    game_map.tiles[key] = tile

            # Show result
            msg = f"Replaced {result.replaced} item(s)"
            if result.exceeded_limit:
                msg += f" (limit of {limit} reached)"

            self._result_label.setText(f"✓ {msg}")

            # Trigger redraw
            if hasattr(self._session, "request_redraw"):
                self._session.request_redraw()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Replacement failed: {e}")

    def set_source_id(self, item_id: int) -> None:
        """Set source item ID (for right-click context)."""
        self._source_spin.setValue(int(item_id))
