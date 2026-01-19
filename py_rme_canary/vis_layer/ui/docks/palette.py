from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget, QLineEdit, QListWidget, QListWidgetItem, QTabWidget, QVBoxLayout, QWidget

from py_rme_canary.logic_layer.brush_definitions import (
    VIRTUAL_DOOR_TOOL_HATCH,
    VIRTUAL_DOOR_TOOL_LOCKED,
    VIRTUAL_DOOR_TOOL_MAGIC,
    VIRTUAL_DOOR_TOOL_NORMAL,
    VIRTUAL_DOOR_TOOL_QUEST,
    VIRTUAL_DOOR_TOOL_WINDOW,
    VIRTUAL_DOODAD_BASE,
    VIRTUAL_HOUSE_BASE,
    VIRTUAL_HOUSE_EXIT_BASE,
    VIRTUAL_MONSTER_BASE,
    VIRTUAL_MONSTER_MAX,
    VIRTUAL_NPC_BASE,
    VIRTUAL_NPC_MAX,
    VIRTUAL_OPTIONAL_BORDER_ID,
    VIRTUAL_SPAWN_MONSTER_TOOL_ID,
    VIRTUAL_SPAWN_NPC_TOOL_ID,
    VIRTUAL_WAYPOINT_BASE,
    VIRTUAL_WAYPOINT_MAX,
    VIRTUAL_ZONE_BASE,
    monster_virtual_id,
    npc_virtual_id,
    waypoint_virtual_id,
)

from py_rme_canary.core.io.creatures_xml import load_monster_names, load_npc_names

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


@dataclass(slots=True)
class PaletteDock:
    dock: QDockWidget
    tabs: QTabWidget
    filter_edit: QLineEdit
    list_widget: QListWidget
    key_by_index: dict[int, str]


class PaletteManager:
    """Manages legacy-style Window palettes using a modern dock UI.

    This keeps `QtMapEditor` smaller and preserves backwards-compatibility by
    exposing the primary palette's widgets as `editor.brush_filter` and
    `editor.brush_list`.
    """

    def __init__(self, editor: "QtMapEditor") -> None:
        self._editor = editor
        self._palettes: list[PaletteDock] = []
        self._palette_counter: int = 0
        self._primary: PaletteDock | None = None

    @property
    def primary(self) -> PaletteDock | None:
        return self._primary

    @property
    def current_palette_name(self) -> str:
        """Return the selected palette key for the primary palette.

        This is a small convenience/compat shim used by UI smoke tests and
        legacy-style helpers.
        """

        primary = self._primary
        if primary is None:
            return ""
        idx = int(primary.tabs.currentIndex())
        return str(primary.key_by_index.get(idx, ""))

    def palette_keys(self) -> list[tuple[str, str]]:
        return [
            ("terrain", "Terrain"),
            ("doodad", "Doodad"),
            ("item", "Item"),
            ("recent", "Recent"),
            ("house", "House"),
            ("creature", "Creature"),
            ("npc", "Npc"),
            ("waypoint", "Waypoint"),
            ("zones", "Zones"),
            ("raw", "RAW"),
        ]

    def allowed_brush_types(self, palette_key: str) -> set[str] | None:
        key = (palette_key or "").strip().lower()
        mapping: dict[str, set[str]] = {
            "terrain": {"ground", "carpet"},
            # Doodad palette is backed by materials XML doodad brushes when available.
            # (Fallback behavior: show wall brushes and wrap them as doodads.)
            "doodad": {"wall"},
            "item": {"carpet"},
            "house": {"house"},
        }
        return mapping.get(key)

    def build_primary(self, *, title: str = "Palette") -> PaletteDock:
        pal = self._create_dock(title=title, make_primary=True)
        self._primary = pal
        return pal

    def create_additional(self, _checked: bool = False) -> PaletteDock:
        pal = self._create_dock(title="Palette", make_primary=False)
        primary = self._primary
        if primary is not None:
            try:
                pal.tabs.setCurrentIndex(int(primary.tabs.currentIndex()))
            except Exception:
                pass
        pal.dock.show()
        pal.dock.raise_()
        pal.filter_edit.setFocus()
        pal.filter_edit.selectAll()
        return pal

    def select_palette(self, palette_key: str) -> None:
        primary = self._primary
        if primary is None:
            return
        key = (palette_key or "").strip().lower()

        for idx, k in primary.key_by_index.items():
            if k == key:
                primary.tabs.setCurrentIndex(int(idx))
                break

        primary.dock.show()
        primary.dock.raise_()

        if key == "raw":
            try:
                self._editor.brush_id_entry.setFocus()
                self._editor.brush_id_entry.selectAll()
            except Exception:
                pass
        else:
            primary.filter_edit.setFocus()
            primary.filter_edit.selectAll()

        self.refresh_list(primary)

    def refresh_primary_list(self) -> None:
        if self._primary is not None:
            self.refresh_list(self._primary)

    def refresh_list(self, palette: PaletteDock) -> None:
        editor = self._editor
        q = (palette.filter_edit.text() or "").strip().lower()
        palette_key = palette.key_by_index.get(int(palette.tabs.currentIndex()), "")
        allowed = self.allowed_brush_types(palette_key)
        all_ids = sorted(getattr(editor.brush_mgr, "_brushes", {}).keys())

        palette.list_widget.blockSignals(True)
        palette.list_widget.clear()

        key_norm = str(palette_key or "").strip().lower()
        if key_norm == "doodad":
            # Prefer real doodad brushes parsed from materials XML.
            doodads = []
            try:
                if hasattr(editor.brush_mgr, "ensure_doodads_loaded"):
                    editor.brush_mgr.ensure_doodads_loaded(os.path.join("data", "materials", "brushs.xml"))
                doodads = list(getattr(editor.brush_mgr, "iter_doodad_brushes")())
            except Exception:
                doodads = []

            if doodads:
                for sid, name in sorted(doodads, key=lambda t: str(t[1]).lower()):
                    sid = int(sid)
                    if sid <= 0:
                        continue
                    text = f"{int(sid)}: {str(name).strip()}"
                    if q and (q not in text.lower()):
                        continue
                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, int(VIRTUAL_DOODAD_BASE + int(sid)))
                    palette.list_widget.addItem(item)

                palette.list_widget.blockSignals(False)
                return

        if key_norm == "terrain":
            # Legacy-style tool: Optional Border (gravel). Implemented as a virtual brush.
            label = "Optional Border Tool"
            if (not q) or (q in label.lower()):
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, int(VIRTUAL_OPTIONAL_BORDER_ID))
                palette.list_widget.addItem(item)

            # Legacy-style door brushes (MVP): place/toggle doors via virtual tools.
            door_tools: list[tuple[str, int]] = [
                ("Door Tool: Normal", int(VIRTUAL_DOOR_TOOL_NORMAL)),
                ("Door Tool: Locked", int(VIRTUAL_DOOR_TOOL_LOCKED)),
                ("Door Tool: Magic", int(VIRTUAL_DOOR_TOOL_MAGIC)),
                ("Door Tool: Quest", int(VIRTUAL_DOOR_TOOL_QUEST)),
                ("Door Tool: Window", int(VIRTUAL_DOOR_TOOL_WINDOW)),
                ("Door Tool: Hatch", int(VIRTUAL_DOOR_TOOL_HATCH)),
            ]
            for text, sid in door_tools:
                if q and (q not in text.lower()):
                    continue
                it = QListWidgetItem(text)
                it.setData(Qt.ItemDataRole.UserRole, int(sid))
                palette.list_widget.addItem(it)

        if key_norm == "zones":
            zones = getattr(getattr(editor, "session", None), "game_map", None)
            zones = getattr(zones, "zones", None) or {}
            for z in sorted(zones.values(), key=lambda zz: int(getattr(zz, "id", 0))):
                zid = int(getattr(z, "id", 0))
                if zid <= 0:
                    continue
                name = str(getattr(z, "name", "") or "").strip()
                text = f"{int(zid)}: {name}" if name else str(int(zid))
                if q:
                    hay = f"{int(zid)} {name}".lower()
                    if q not in hay:
                        continue
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, int(VIRTUAL_ZONE_BASE + zid))
                palette.list_widget.addItem(item)

        elif key_norm == "waypoint":
            gm = getattr(getattr(editor, "session", None), "game_map", None)
            waypoints = getattr(gm, "waypoints", None) or {}

            # Build stable ids for all waypoints independent of filtering.
            used: set[int] = set()
            names = sorted((str(k) for k in waypoints.keys()), key=lambda s: s.lower())
            name_to_vid: dict[str, int] = {}
            for nm in names:
                try:
                    vid = int(waypoint_virtual_id(nm, used=used))
                except Exception:
                    continue
                name_to_vid[str(nm)] = int(vid)

            for nm in names:
                pos = waypoints.get(nm)
                if pos is None:
                    continue
                text = f"{nm} @ ({int(getattr(pos, 'x', 0))},{int(getattr(pos, 'y', 0))},{int(getattr(pos, 'z', 0))})"
                if q and (q not in text.lower()):
                    continue

                vid = name_to_vid.get(nm)
                if vid is None or not (
                    VIRTUAL_WAYPOINT_BASE <= int(vid) < VIRTUAL_WAYPOINT_BASE + int(VIRTUAL_WAYPOINT_MAX)
                ):
                    continue

                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, int(vid))
                palette.list_widget.addItem(item)

        elif key_norm == "creature":
            # Legacy parity (MVP): monster placement is implemented as spawn XML entries
            # (map-level), so we expose monsters via virtual ids.
            label = "Spawn Area Tool"
            text = f"Monster {label}"
            if (not q) or (q in text.lower()):
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, int(VIRTUAL_SPAWN_MONSTER_TOOL_ID))
                palette.list_widget.addItem(item)

            # Build stable ids for all monsters independent of filtering.
            used: set[int] = set()
            names = tuple(load_monster_names())
            name_to_vid: dict[str, int] = {}
            for nm in names:
                try:
                    vid = int(monster_virtual_id(str(nm), used=used))
                except Exception:
                    continue
                name_to_vid[str(nm)] = int(vid)

            for nm in names:
                if q and (q not in str(nm).lower()):
                    continue
                vid = name_to_vid.get(str(nm))
                if vid is None or not (VIRTUAL_MONSTER_BASE <= int(vid) < VIRTUAL_MONSTER_BASE + int(VIRTUAL_MONSTER_MAX)):
                    continue
                item = QListWidgetItem(str(nm))
                item.setData(Qt.ItemDataRole.UserRole, int(vid))
                palette.list_widget.addItem(item)

        elif key_norm == "npc":
            label = "Spawn Area Tool"
            text = f"NPC {label}"
            if (not q) or (q in text.lower()):
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, int(VIRTUAL_SPAWN_NPC_TOOL_ID))
                palette.list_widget.addItem(item)

            # Build stable ids for all NPCs independent of filtering.
            used = set()
            names = tuple(load_npc_names())
            name_to_vid: dict[str, int] = {}
            for nm in names:
                try:
                    vid = int(npc_virtual_id(str(nm), used=used))
                except Exception:
                    continue
                name_to_vid[str(nm)] = int(vid)

            for nm in names:
                if q and (q not in str(nm).lower()):
                    continue
                vid = name_to_vid.get(str(nm))
                if vid is None or not (VIRTUAL_NPC_BASE <= int(vid) < VIRTUAL_NPC_BASE + int(VIRTUAL_NPC_MAX)):
                    continue
                item = QListWidgetItem(str(nm))
                item.setData(Qt.ItemDataRole.UserRole, int(vid))
                palette.list_widget.addItem(item)

        elif key_norm == "house":
            houses = getattr(getattr(editor, "session", None), "game_map", None)
            houses = getattr(houses, "houses", None) or {}
            for h in sorted(houses.values(), key=lambda hh: int(getattr(hh, "id", 0))):
                hid = int(getattr(h, "id", 0))
                if hid <= 0:
                    continue
                name = str(getattr(h, "name", "") or "").strip()
                text = f"{int(hid)}: {name}" if name else str(int(hid))
                if q:
                    hay = f"{int(hid)} {name}".lower()
                    if q not in hay:
                        continue
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, int(VIRTUAL_HOUSE_BASE + hid))
                palette.list_widget.addItem(item)

                # Legacy parity (MVP): House Exit brush.
                # Exposed as a second entry per house to avoid adding extra toggle UI.
                exit_text = f"Exit: {int(hid)}: {name}" if name else f"Exit: {int(hid)}"
                exit_item = QListWidgetItem(exit_text)
                exit_item.setData(Qt.ItemDataRole.UserRole, int(VIRTUAL_HOUSE_EXIT_BASE + hid))
                palette.list_widget.addItem(exit_item)

        elif key_norm == "recent":
            session = getattr(editor, "session", None)
            recent = list(getattr(session, "recent_brushes", []) or [])
            for sid in recent:
                try:
                    bd = editor.brush_mgr.get_brush(int(sid))
                except Exception:
                    bd = None
                btype = str(getattr(bd, "brush_type", "") or "").strip().lower() if bd is not None else ""
                name = str(getattr(bd, "name", "") or "").strip() if bd is not None else ""
                text = f"{int(sid)}: {name}" if name else str(int(sid))
                if btype:
                    text = f"{text} ({btype})"

                if q and (q not in text.lower()):
                    continue
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, int(sid))
                palette.list_widget.addItem(item)
        else:
            for sid in all_ids:
                bd = editor.brush_mgr.get_brush(int(sid))
                if bd is None:
                    continue
                btype = str(getattr(bd, "brush_type", "") or "").strip().lower()
                if allowed is not None and btype and btype not in allowed:
                    continue

                name = str(getattr(bd, "name", "") or "").strip()
                text = f"{int(sid)}: {name}" if name else str(int(sid))

                if q:
                    hay = f"{int(sid)} {name} {btype}".lower()
                    if q not in hay:
                        continue

                item = QListWidgetItem(text)
                if key_norm == "doodad":
                    item.setData(Qt.ItemDataRole.UserRole, int(VIRTUAL_DOODAD_BASE + int(sid)))
                else:
                    item.setData(Qt.ItemDataRole.UserRole, int(sid))
                palette.list_widget.addItem(item)

        palette.list_widget.blockSignals(False)

    def _create_dock(self, title: str, *, make_primary: bool) -> PaletteDock:
        self._palette_counter = int(self._palette_counter) + 1
        dock_title = str(title)
        if not make_primary and self._palette_counter > 1:
            dock_title = f"{dock_title} ({self._palette_counter})"

        dock = QDockWidget(dock_title, self._editor)
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        panel = QWidget(dock)
        v = QVBoxLayout(panel)
        v.setContentsMargins(8, 8, 8, 8)

        tabs = QTabWidget(panel)
        tabs.setDocumentMode(True)
        tabs.setMovable(False)
        key_by_index: dict[int, str] = {}
        for idx, (key, label) in enumerate(self.palette_keys()):
            tabs.addTab(QWidget(), label)
            key_by_index[int(idx)] = str(key)
        v.addWidget(tabs)

        filter_edit = QLineEdit(panel)
        filter_edit.setPlaceholderText("search…")
        v.addWidget(filter_edit)

        list_widget = QListWidget(panel)
        v.addWidget(list_widget, stretch=1)

        dock.setWidget(panel)
        self._editor.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

        pal = PaletteDock(
            dock=dock, tabs=tabs, filter_edit=filter_edit, list_widget=list_widget, key_by_index=key_by_index
        )
        self._palettes.append(pal)

        tabs.currentChanged.connect(lambda _i: self.refresh_list(pal))
        filter_edit.textChanged.connect(lambda _t: self.refresh_list(pal))
        list_widget.itemSelectionChanged.connect(lambda: self._on_selected(list_widget))

        if make_primary:
            # Backwards-compatible attributes.
            self._editor.dock_brushes = dock
            self._editor.brush_filter = filter_edit
            self._editor.brush_list = list_widget
            self._editor._primary_palette = pal

        self.refresh_list(pal)
        return pal

    def _on_selected(self, list_widget: QListWidget) -> None:
        items = list_widget.selectedItems()
        if not items:
            return
        sid = items[0].data(Qt.ItemDataRole.UserRole)
        if sid is None:
            return
        self._editor._set_selected_brush_id(int(sid))
