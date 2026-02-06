"""Modern Palette Dock.

Combines Categorized Tabs, Card View (ModernPaletteWidget), and Tool Options.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget, QSplitter, QTabWidget, QVBoxLayout, QWidget

from py_rme_canary.vis_layer.ui.docks.modern_palette import BrushCardData, ModernPaletteWidget
from py_rme_canary.vis_layer.ui.docks.modern_tool_options import ModernToolOptionsWidget
from py_rme_canary.vis_layer.ui.docks.palette import _resolve_materials_brushs_path

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class ModernPaletteDock(QDockWidget):
    """Modern replacement for the palette dock."""

    def __init__(self, editor: QtMapEditor, parent: QWidget | None = None) -> None:
        super().__init__("Palette", parent)
        self.editor = editor

        self._setup_ui()
        self._connect_signals()
        self._populate_tabs()

    def _setup_ui(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Splitter to resize between palette and options
        self.splitter = QSplitter(Qt.Orientation.Vertical)

        # 1. Palette Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.splitter.addWidget(self.tabs)

        # 2. Tool Options
        self.tool_options = ModernToolOptionsWidget()
        self.splitter.addWidget(self.tool_options)

        # Default split size
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        layout.addWidget(self.splitter)
        self.setWidget(container)

    def _connect_signals(self) -> None:
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Tool Options -> Editor
        self.tool_options.size_changed.connect(
            lambda s: self.editor.set_brush_size(s) if hasattr(self.editor, "set_brush_size") else None
        )
        self.tool_options.shape_changed.connect(
            lambda s: self.editor.set_brush_shape(s) if hasattr(self.editor, "set_brush_shape") else None
        )

    def _populate_tabs(self) -> None:
        """Create tabs for each category."""
        categories = [
            ("Terrain", "terrain"),
            ("Doodad", "doodad"),
            ("Item", "item"),
            ("Recent", "recent"),
            ("House", "house"),
            ("Creature", "creature"),
            ("NPC", "npc"),
            ("Zone", "zones"),
            ("Waypoints", "waypoint"),
            ("RAW", "raw"),
        ]

        self._palette_widgets: dict[str, ModernPaletteWidget] = {}

        for label, key in categories:
            sprite_lookup = None
            if hasattr(self.editor, "_sprite_pixmap_for_server_id"):

                def _lookup(sid: int, size: int):
                    return self.editor._sprite_pixmap_for_server_id(int(sid), tile_px=int(size))

                sprite_lookup = _lookup
            widget = ModernPaletteWidget(sprite_lookup=sprite_lookup)
            # We will populate the widget when tab is selected or initially
            widget.brush_selected.connect(self._on_brush_selected)

            self.tabs.addTab(widget, label)
            self._palette_widgets[key] = widget

            # Store key on widget for retrieval
            widget.setProperty("palette_key", key)

    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change to update options and populate list if needed."""
        widget = self.tabs.widget(index)
        if not isinstance(widget, ModernPaletteWidget):
            return

        key = str(widget.property("palette_key") or "")

        # Update Tool Options visibility
        self.tool_options.set_brush_type(key)

        # Populate brushes if empty (Lazy loading)
        # Note: In a real implementation, we would fetch brushes from editor.brush_mgr
        # using the 'key' to filter.
        # For now, we assume refresh_list logic will be migrated here or called externally.
        self._refresh_palette_content(key, widget)

    def _on_brush_selected(self, brush_id: int) -> None:
        """Forward selection to editor."""
        # Using private method for now as per legacy interface, ideally public
        if hasattr(self.editor, "_set_selected_brush_id"):
            self.editor._set_selected_brush_id(brush_id)

    def _refresh_palette_content(self, key: str, widget: ModernPaletteWidget) -> None:
        """Fetch brushes from editor and populate widget."""
        from py_rme_canary.core.io.creatures_xml import load_monster_names, load_npc_names
        from py_rme_canary.logic_layer.brush_definitions import (
            VIRTUAL_DOODAD_BASE,
            VIRTUAL_DOOR_TOOL_HATCH,
            VIRTUAL_DOOR_TOOL_LOCKED,
            VIRTUAL_DOOR_TOOL_MAGIC,
            VIRTUAL_DOOR_TOOL_NORMAL,
            VIRTUAL_DOOR_TOOL_QUEST,
            VIRTUAL_DOOR_TOOL_WINDOW,
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

        editor = self.editor
        key_norm = key.strip().lower()
        brushes: list[BrushCardData] = []

        # 1. Doodads
        if key_norm == "doodad":
            doodads = []
            try:
                if hasattr(editor.brush_mgr, "ensure_doodads_loaded"):
                    materials_path = _resolve_materials_brushs_path()
                    if materials_path:
                        editor.brush_mgr.ensure_doodads_loaded(materials_path)
                doodads = list(editor.brush_mgr.iter_doodad_brushes())
            except Exception:
                doodads = []

            for sid, name in sorted(doodads, key=lambda t: str(t[1]).lower()):
                sid = int(sid)
                if sid <= 0:
                    continue
                brushes.append(
                    BrushCardData(
                        brush_id=int(VIRTUAL_DOODAD_BASE + sid),
                        name=str(name).strip(),
                        brush_type="doodad",
                        sprite_id=sid,
                    )
                )

        # 2. Terrain
        elif key_norm == "terrain":
            # Optional Border
            brushes.append(
                BrushCardData(brush_id=int(VIRTUAL_OPTIONAL_BORDER_ID), name="Optional Border", brush_type="terrain")
            )

            # Doors
            door_tools = [
                ("Door: Normal", VIRTUAL_DOOR_TOOL_NORMAL),
                ("Door: Locked", VIRTUAL_DOOR_TOOL_LOCKED),
                ("Door: Magic", VIRTUAL_DOOR_TOOL_MAGIC),
                ("Door: Quest", VIRTUAL_DOOR_TOOL_QUEST),
                ("Door: Window", VIRTUAL_DOOR_TOOL_WINDOW),
                ("Door: Hatch", VIRTUAL_DOOR_TOOL_HATCH),
            ]
            for name, vid in door_tools:
                brushes.append(BrushCardData(brush_id=int(vid), name=name, brush_type="terrain"))

            # Standard Terrain Brushes
            # We filter editor.brush_mgr for 'ground' type
            all_ids = sorted(getattr(editor.brush_mgr, "_brushes", {}).keys())
            for sid in all_ids:
                bd = editor.brush_mgr.get_brush(int(sid))
                if bd and getattr(bd, "brush_type", "") == "ground":
                    brushes.append(
                        BrushCardData(
                            brush_id=int(sid),
                            name=str(getattr(bd, "name", "")),
                            brush_type="ground",
                            sprite_id=int(getattr(bd, "server_id", 0)),
                        )
                    )

        # 3. Creatures (Monsters)
        elif key_norm == "creature":
            brushes.append(
                BrushCardData(brush_id=int(VIRTUAL_SPAWN_MONSTER_TOOL_ID), name="Spawn Area", brush_type="spawn")
            )

            used: set[int] = set()
            names = sorted(load_monster_names())
            for nm in names:
                try:
                    vid = int(monster_virtual_id(str(nm), used=used))
                    if VIRTUAL_MONSTER_BASE <= vid < VIRTUAL_MONSTER_BASE + VIRTUAL_MONSTER_MAX:
                        brushes.append(BrushCardData(brush_id=vid, name=str(nm), brush_type="monster"))
                except Exception:
                    continue

        # 4. NPCs
        elif key_norm == "npc":
            brushes.append(BrushCardData(brush_id=int(VIRTUAL_SPAWN_NPC_TOOL_ID), name="NPC Area", brush_type="spawn"))

            used = set()
            names = sorted(load_npc_names())
            for nm in names:
                try:
                    vid = int(npc_virtual_id(str(nm), used=used))
                    if VIRTUAL_NPC_BASE <= vid < VIRTUAL_NPC_BASE + VIRTUAL_NPC_MAX:
                        brushes.append(BrushCardData(brush_id=vid, name=str(nm), brush_type="npc"))
                except Exception:
                    continue

        # 5. House
        elif key_norm == "house":
            houses = getattr(getattr(editor, "session", None), "game_map", None)
            houses = getattr(houses, "houses", None) or {}
            for h in sorted(houses.values(), key=lambda hh: int(getattr(hh, "id", 0))):
                hid = int(getattr(h, "id", 0))
                if hid <= 0:
                    continue
                name = str(getattr(h, "name", "") or "").strip()
                label = f"{int(hid)}: {name}" if name else str(int(hid))
                brushes.append(BrushCardData(brush_id=int(VIRTUAL_HOUSE_BASE + hid), name=label, brush_type="house"))
                exit_label = f"Exit: {int(hid)}: {name}" if name else f"Exit: {int(hid)}"
                brushes.append(
                    BrushCardData(
                        brush_id=int(VIRTUAL_HOUSE_EXIT_BASE + hid),
                        name=exit_label,
                        brush_type="house_exit",
                    )
                )

        # 6. Waypoints
        elif key_norm == "waypoint":
            gm = getattr(getattr(editor, "session", None), "game_map", None)
            waypoints = getattr(gm, "waypoints", None) or {}
            used: set[int] = set()
            names = sorted((str(k) for k in waypoints), key=lambda s: s.casefold())
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
                vid = name_to_vid.get(nm)
                if vid is None or not (
                    VIRTUAL_WAYPOINT_BASE <= int(vid) < VIRTUAL_WAYPOINT_BASE + int(VIRTUAL_WAYPOINT_MAX)
                ):
                    continue
                label = f"{nm} @ ({int(getattr(pos, 'x', 0))},{int(getattr(pos, 'y', 0))},{int(getattr(pos, 'z', 0))})"
                brushes.append(BrushCardData(brush_id=int(vid), name=label, brush_type="waypoint"))

        # 7. Zones
        elif key_norm == "zones":
            zones = getattr(getattr(editor, "session", None), "game_map", None)
            zones = getattr(zones, "zones", None) or {}
            for z in sorted(zones.values(), key=lambda zz: int(getattr(zz, "id", 0))):
                zid = int(getattr(z, "id", 0))
                if zid <= 0:
                    continue
                name = str(getattr(z, "name", "") or "").strip()
                label = f"{int(zid)}: {name}" if name else str(int(zid))
                brushes.append(BrushCardData(brush_id=int(VIRTUAL_ZONE_BASE + zid), name=label, brush_type="zone"))

        # 8. Recent
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
                label = f"{int(sid)}: {name}" if name else str(int(sid))
                if btype:
                    label = f"{label} ({btype})"
                brushes.append(
                    BrushCardData(
                        brush_id=int(sid),
                        name=label,
                        brush_type=btype,
                        sprite_id=int(getattr(bd, "server_id", 0)) if bd is not None else None,
                    )
                )

        # 5. Items (and others)
        else:
            # Fallback for Item, RAW, etc.
            allowed_types = {
                "item": {"carpet", "table"},  # Simplified mapping
                "raw": set(),  # RAW usually handled differently
            }.get(key_norm)

            all_ids = sorted(getattr(editor.brush_mgr, "_brushes", {}).keys())
            for sid in all_ids:
                bd = editor.brush_mgr.get_brush(int(sid))
                if not bd:
                    continue

                btype = str(getattr(bd, "brush_type", "")).lower()

                # If filtered by allowed types
                if allowed_types is not None and btype not in allowed_types:
                    continue

                # For Generic/Other categories, include if type matches or if no filter
                if key_norm == "item" or key_norm == "raw" or key_norm not in ["terrain", "doodad", "creature", "npc"]:
                    brushes.append(
                        BrushCardData(
                            brush_id=int(sid),
                            name=str(getattr(bd, "name", "")),
                            brush_type=btype,
                            sprite_id=int(getattr(bd, "server_id", 0)),
                        )
                    )

        widget.set_brushes(brushes)
