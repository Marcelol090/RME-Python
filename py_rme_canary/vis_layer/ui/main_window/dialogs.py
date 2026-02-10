from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.item import Position
from py_rme_canary.logic_layer.map_statistics import compute_map_statistics, format_map_statistics_report


@dataclass(slots=True)
class FindItemResult:
    server_id: int
    query_mode: str = "server_id"
    query_value: int = 0
    resolved: bool = True
    error: str = ""


class FindItemDialog(QDialog):
    def __init__(self, parent=None, *, title: str = "Find Item") -> None:
        super().__init__(parent)
        self.setWindowTitle(str(title))
        self.setModal(True)
        self.setMinimumWidth(_scale_dip(self, 360))

        self._mode_combo = QComboBox(self)
        self._mode_combo.addItem("Server ID", "server_id")
        self._mode_combo.addItem("Client ID", "client_id")
        self._id_spin = QSpinBox(self)
        self._id_spin.setRange(0, 10_000_000)
        self._id_spin.setValue(0)
        self._id_spin.setToolTip("Use Server ID by default. Choose Client ID when working with modern/canary assets.")

        form = QFormLayout()
        form.addRow("Search by:", self._mode_combo)
        form.addRow("ID:", self._id_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(buttons)

    def result_value(self) -> FindItemResult:
        query_value = int(self._id_spin.value())
        query_mode = str(self._mode_combo.currentData() or "server_id")

        if query_mode == "server_id":
            return FindItemResult(
                server_id=int(query_value),
                query_mode=query_mode,
                query_value=int(query_value),
                resolved=True,
                error="",
            )

        mapped = _resolve_server_id_from_client_id(int(query_value))
        if mapped is None:
            return FindItemResult(
                server_id=0,
                query_mode=query_mode,
                query_value=int(query_value),
                resolved=False,
                error=f"No ServerID mapping for ClientID {int(query_value)}.",
            )
        return FindItemResult(
            server_id=int(mapped),
            query_mode=query_mode,
            query_value=int(query_value),
            resolved=True,
            error="",
        )


@dataclass(slots=True)
class FindEntityResult:
    mode: str  # "item", "house", "monster", "npc"
    query_id: int = 0
    query_mode: str = "server_id"
    query_name: str = ""


class FindEntityDialog(QDialog):
    def __init__(self, parent=None, *, title: str = "Find...") -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(_scale_dip(self, 380))

        self._tabs = QTabWidget(self)

        # -- Item Tab --
        self._tab_item = QWidget()
        self._item_mode_combo = QComboBox()
        self._item_mode_combo.addItem("Server ID", "server_id")
        self._item_mode_combo.addItem("Client ID", "client_id")
        self._item_id_spin = QSpinBox()
        self._item_id_spin.setRange(0, 99999)
        l_item = QFormLayout(self._tab_item)
        l_item.addRow("Search by:", self._item_mode_combo)
        l_item.addRow("Item ID:", self._item_id_spin)
        self._tabs.addTab(self._tab_item, "Item")

        # -- Creature Tab (Monster/NPC) --
        self._tab_creature = QWidget()
        self._creature_name_edit = QLineEdit()
        self._creature_name_edit.setPlaceholderText("Name (e.g. Dragon)")
        self._creature_type_combo = QListWidget()  # Or checkboxes
        # Let's simplify: just a name search, check both or select type?
        # Rolling with separate tabs strictly or a combo for type?
        # User asked for "Find Npc", "Find Monster". Let's do distinct tabs for clarity or radio buttons.
        # Actually rollout plan separates them. Let's make "Monster" and "Npc" separate modes in logic but maybe same tab?
        # Let's stick to tabs for distinct search modes.
        l_creature = QVBoxLayout(self._tab_creature)
        l_creature.addWidget(QLabel("Name:"))
        l_creature.addWidget(self._creature_name_edit)
        self._tabs.addTab(self._tab_creature, "Creature")

        # -- House Tab --
        self._tab_house = QWidget()
        self._house_name_edit = QLineEdit()
        self._house_name_edit.setPlaceholderText("Name...")
        l_house = QVBoxLayout(self._tab_house)
        l_house.addWidget(QLabel("House Name:"))
        l_house.addWidget(self._house_name_edit)
        self._tabs.addTab(self._tab_house, "House")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self._tabs)
        layout.addWidget(buttons)

    def set_mode(self, mode: str) -> None:
        """Set current search tab by mode name."""
        normalized = str(mode).strip().lower()
        index_by_mode = {"item": 0, "creature": 1, "house": 2}
        idx = index_by_mode.get(normalized)
        if idx is not None:
            self._tabs.setCurrentIndex(idx)

    def result_value(self) -> FindEntityResult:
        idx = self._tabs.currentIndex()
        title = self._tabs.tabText(idx)

        if title == "Item":
            return FindEntityResult(
                mode="item",
                query_id=int(self._item_id_spin.value()),
                query_mode=str(self._item_mode_combo.currentData() or "server_id"),
            )
        elif title == "Creature":
            return FindEntityResult(mode="creature", query_name=self._creature_name_edit.text())
        elif title == "House":
            return FindEntityResult(mode="house", query_name=self._house_name_edit.text())

        return FindEntityResult(mode="unknown")


def _resolve_server_id_from_client_id(client_id: int) -> int | None:
    if int(client_id) <= 0:
        return None

    from py_rme_canary.logic_layer.asset_manager import AssetManager

    asset_mgr = AssetManager.instance()
    mapper = getattr(asset_mgr, "_id_mapper", None)
    if mapper is not None and hasattr(mapper, "get_server_id"):
        try:
            mapped = mapper.get_server_id(int(client_id))
            if mapped is not None and int(mapped) > 0:
                return int(mapped)
        except Exception:
            pass

    items_xml = getattr(asset_mgr, "_items_xml", None)
    if items_xml is not None and hasattr(items_xml, "get_server_id"):
        try:
            mapped = items_xml.get_server_id(int(client_id))
            if mapped is not None and int(mapped) > 0:
                return int(mapped)
        except Exception:
            pass

    return None


def _scale_dip(widget: QWidget, value: int) -> int:
    app = QApplication.instance()
    if app is None:
        return int(value)
    screen = widget.screen() or app.primaryScreen()
    if screen is None:
        return int(value)
    factor = float(screen.logicalDotsPerInch()) / 96.0
    return max(1, int(round(float(value) * max(1.0, factor))))


class ReplaceItemsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Replace Items")
        self.setModal(True)

        self._from_spin = QSpinBox(self)
        self._from_spin.setRange(0, 10_000_000)
        self._to_spin = QSpinBox(self)
        self._to_spin.setRange(0, 10_000_000)

        form = QFormLayout()
        form.addRow("from serverId:", self._from_spin)
        form.addRow("to serverId:", self._to_spin)

        self._scope = QLineEdit(self)
        self._scope.setPlaceholderText("(future) e.g. current floor / selection")
        self._scope.setEnabled(False)
        form.addRow("scope:", self._scope)

        hint = QLabel("Replaces matching items across the map.")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignLeft)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(hint)
        root.addWidget(buttons)

    def values(self) -> tuple[int, int]:
        return int(self._from_spin.value()), int(self._to_spin.value())

    def set_from_id(self, value: int) -> None:
        self._from_spin.setValue(int(value))

    def set_to_id(self, value: int) -> None:
        self._to_spin.setValue(int(value))


class FindPositionsDialog(QDialog):
    def __init__(self, parent, *, title: str, positions: list[Position]) -> None:
        super().__init__(parent)
        self.setWindowTitle(str(title))
        self.setModal(True)

        self._positions = list(positions)

        label = QLabel(f"Results: {len(self._positions)}")
        label.setWordWrap(True)

        self._list = QListWidget(self)
        for pos in self._positions:
            it = QListWidgetItem(f"{int(pos.x)}, {int(pos.y)}, {int(pos.z)}")
            it.setData(Qt.ItemDataRole.UserRole, (int(pos.x), int(pos.y), int(pos.z)))
            self._list.addItem(it)

        if self._list.count() > 0:
            self._list.setCurrentRow(0)

        self._list.itemDoubleClicked.connect(lambda _it: self.accept())

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addWidget(label)
        root.addWidget(self._list)
        root.addWidget(buttons)

    def selected_position(self) -> Position | None:
        it = self._list.currentItem()
        if it is None:
            return None
        data = it.data(Qt.ItemDataRole.UserRole)
        if not data or not isinstance(data, tuple) or len(data) != 3:
            return None
        x, y, z = data
        return Position(x=int(x), y=int(y), z=int(z))


class WaypointQueryDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Find Waypoint")

        self._edit = QLineEdit(self)
        self._edit.setPlaceholderText("Waypoint name contains…")
        self._edit.setClearButtonEnabled(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Waypoint name contains:"))
        layout.addWidget(self._edit)
        layout.addWidget(buttons)

        self._edit.setFocus()

    def query(self) -> str:
        return self._edit.text()


class FindNamedPositionsDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        *,
        title: str,
        items: list[tuple[str, Position]],
    ):
        super().__init__(parent)
        self.setWindowTitle(title)

        self._list = QListWidget(self)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._chosen: tuple[str, Position] | None = None

        for name, pos in items:
            item = QListWidgetItem(f"{name} — {pos.x},{pos.y},{pos.z}")
            item.setData(Qt.ItemDataRole.UserRole, (name, pos))
            self._list.addItem(item)

        self._list.itemDoubleClicked.connect(self._accept_current)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept_current)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self._list)
        layout.addWidget(buttons)

        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def chosen(self) -> tuple[str, Position] | None:
        return self._chosen

    def _accept_current(self) -> None:
        cur = self._list.currentItem()
        if cur is None:
            return
        self._chosen = cur.data(Qt.ItemDataRole.UserRole)
        self.accept()


class MapStatisticsDialog(QDialog):
    def __init__(self, parent: QWidget | None, *, game_map: GameMap) -> None:
        super().__init__(parent)
        self.setWindowTitle("Map Statistics")
        self.setModal(True)

        self._game_map = game_map

        self._text = QPlainTextEdit(self)
        self._text.setReadOnly(True)

        self._btn_refresh = QPushButton("Refresh", self)
        self._btn_export = QPushButton("Export...", self)
        self._btn_close = QPushButton("Close", self)

        self._btn_refresh.clicked.connect(self._refresh)
        self._btn_export.clicked.connect(self._export)
        self._btn_close.clicked.connect(self.accept)

        buttons = QHBoxLayout()
        buttons.addWidget(self._btn_refresh)
        buttons.addWidget(self._btn_export)
        buttons.addStretch(1)
        buttons.addWidget(self._btn_close)

        root = QVBoxLayout(self)
        root.addWidget(self._text)
        root.addLayout(buttons)

        self._refresh()

    def _refresh(self) -> None:
        stats = compute_map_statistics(self._game_map)
        report = format_map_statistics_report(self._game_map, stats)
        self._text.setPlainText(report)

    def _export(self) -> None:
        path, _filter = QFileDialog.getSaveFileName(
            self,
            "Export Statistics",
            "map_statistics.txt",
            "Text files (*.txt);;All files (*)",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._text.toPlainText())
        except OSError as e:
            QMessageBox.critical(self, "Export Failed", str(e))
            return
        QMessageBox.information(self, "Export Complete", "Statistics exported successfully!")


def show_not_implemented(parent: QWidget | None, title: str, detail: str = "") -> None:
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setWindowTitle(title)
    msg.setText("Not implemented yet")
    if detail:
        msg.setInformativeText(detail)
    msg.exec()
