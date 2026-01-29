# Implementation Status & Parity Checklist - py_rme_canary

---

## 🏁 Executive Summary

This document is the **master checklist** for porting and parity between the legacy C++/Lua codebase (`source/`) and the Python implementation (`py_rme_canary/`).

- **Status icons:**
  - ✅ Implemented
  - ❌ Missing/Incomplete
  - ⚠️ Partial/Stub
- **How to use:**
  - Use this checklist to track porting progress and agent actions.
  - For deep-dive analysis, see [ANALISE_FALTANTE.md](ANALISE_FALTANTE.md), [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md), [IMPLEMENTATION_TODO.md](IMPLEMENTATION_TODO.md), [TODO_EXPENSIVE.md](TODO_EXPENSIVE.md).
  - For actionable stubs, use [IMPLEMENTATION_TODO.md](IMPLEMENTATION_TODO.md).

---

## 📊 Parity Table (C++ → Python)

> **Note:** Updated 2025-01-23 after code audit. Paths corrected to reflect actual file locations.

| Area                | Legacy C++/Lua File(s)         | Python Destination                | Status   | Notes/Links |
|---------------------|-------------------------------|-----------------------------------|----------|-------------|
| Brushes (core)      | brush.cpp, ground_brush.cpp   | logic_layer/brush_definitions.py  | ✅       | Full MVP, see TODO for advanced |
| WallBrush           | wall_brush.cpp                | logic_layer/brush_definitions.py  | ✅       |             |
| Auto-border         | auto_border.cpp               | logic_layer/auto_border.py        | ✅       |             |
| BrushManager        | brush_manager.cpp             | logic_layer/brush_definitions.py  | ✅       |             |
| TableBrush          | table_brush.cpp               | logic_layer/brush_definitions.py  | ✅       | `TableBrushSpec` + tests; materials XML parsing parity verified (2026-01-29) |
| CarpetBrush         | carpet_brush.cpp              | logic_layer/brush_definitions.py  | ✅       | `CarpetBrushSpec` + tests; materials XML parsing parity verified (2026-01-29) |
| DoorBrush           | door_brush.cpp                | logic_layer/door_brush.py         | ✅       | `DoorBrush` class + `switch_door()` + tests |
| DoodadBrush         | doodad_brush.cpp              | logic_layer/brush_definitions.py  | ✅       | `DoodadBrushSpec` + erase-like + unique-item protection |
| HouseBrush          | house_brush.cpp               | logic_layer/house_brush.py     | ✅       | Complete implementation with TDD (2026-01-26) |
| HouseExitBrush      | house_exit_brush.cpp          | logic_layer/house_exit_brush.py | ✅       | Complete implementation with TDD (2026-01-26) |
| WaypointBrush       | waypoint_brush.cpp            | logic_layer/waypoint_brush.py | ✅       | Complete implementation (2026-01-26) |
| MonsterBrush        | monster_brush.cpp             | logic_layer/monster_brush.py      | ✅       | `MonsterBrush` class + tests |
| NpcBrush            | npc_brush.cpp                 | logic_layer/npc_brush.py          | ✅       | `NpcBrush` class + tests |
| SpawnMonster/Npc    | spawn_monster_brush.cpp       | logic_layer/spawn_monster_brush.py + logic_layer/spawn_npc_brush.py | ✅ | Complete implementation (2026-01-26) |
| FlagBrush           | flag_brush.cpp                | logic_layer/flag_brush.py         | ✅       | `FlagBrush` class + tests |
| ZoneBrush           | zone_brush.cpp                | vis_layer/ui/dialogs/zone_town_dialogs.py | ✅ | Implemented in `ZoneListDialog` (2026-01-26) |
| OptionalBorderBrush | optional_border_brush.cpp     | logic_layer/optional_border_brush.py | ✅       | Basic implementation (2026-01-26) |
| EraserBrush         | eraser_brush.cpp              | logic_layer/eraser_brush.py       | ✅       | `EraserBrush` class + tests |
| Recent Brushes      | palette_window.cpp            | vis_layer/ui/widgets/quick_access.py | ✅       | `QuickAccessBar` implemented (2026-01-26) |
| BrushShape/Size     | map_display.cpp               | vis_layer/ui/widgets/brush_toolbar.py | ✅       | `BrushToolbar` implemented with shapes/sizes (2026-01-26) |
| Brush Variation     | brush.cpp                     | logic_layer/brush_definitions.py  | ⚠️       | MVP implemented; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| Brush Thickness     | brush.cpp                     | logic_layer/brush_definitions.py  | ⚠️       | MVP implemented; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| Drag/Smear          | brush.cpp                     | logic_layer/brush_definitions.py  | ⚠️       | Partial (select tools); see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| Border Builder      | border_builder.cpp            | logic_layer/auto_border.py        | ⚠️       | Registry/logica avançada em progresso |
| Border Groups       | logic_layer/borders/border_groups.py | logic_layer/borders/border_groups.py | ✅ | `BorderGroupRegistry` implemented |
| Border Friends/Hate | border_friends.cpp            | logic_layer/borders/border_friends.py | ✅   | Friend/enemy mask support |
| Ground Equivalents  | ground_equivalents.cpp        | logic_layer/borders/ground_equivalents.py | ✅ | Equivalências aplicadas |
| EditorSession       | editor_session.cpp            | logic_layer/editor_session.py     | ✅       |             |
| Selection Modes     | selection.cpp                  | logic_layer/session/selection.py  | ✅       | COMPENSATE/CURRENT/LOWER/VISIBLE wired to UI (2026-01-26) |
| Clipboard           | copybuffer.cpp                 | logic_layer/session/clipboard.py  | ✅       | Full system with history/transforms (2026-01-26) |
| Undo/Redo           | action.cpp                     | vis_layer/ui/widgets/undo_redo.py | ✅       | `UndoRedoPanel` implemented (2026-01-26) |
| Mouse Gestures      | gestures.cpp                   | logic_layer/session/gestures.py   | ✅       |             |
| Move Selection      | selection.cpp                  | logic_layer/session/move.py       | ✅       |             |
| Borderize Selection | borderize.cpp                  | logic_layer/session/editor.py     | ✅       | `borderize_selection()` implemented |
| Randomize Selection | randomize.cpp                  | logic_layer/session/editor.py     | ✅       | `randomize_selection()` + `randomize_map()` implemented |
| Duplicate Selection | selection.cpp                  | vis_layer/ui/main_window/qt_map_editor_edit.py| ✅ | `_duplicate_selection()` implemented |
| Move Selection Z    | selection.cpp                  | vis_layer/ui/main_window/qt_map_editor_edit.py| ✅ | `_move_selection_z()` implemented |
| Clear Selection     | selection.cpp                  | logic_layer/session/selection.py  | ⚠️       | Partial, see [ANALISE_FALTANTE.md](ANALISE_FALTANTE.md) |
| ActionQueue         | action_queue.cpp               | logic_layer/session/action_queue.py| ✅      | Stacking delay, CompositeAction, labels, timer reset implemented |
| NetworkedActionQueue| live_action.cpp                | core/protocols/action_queue.py    | ❌       |             |
| Action Types        | action.h (ActionIdentifier)    | logic_layer/session/action_queue.py| ✅       | `ActionType` enum with 41 types (PAINT, DELETE_SELECTION, MOVE_SELECTION, BORDERIZE_SELECTION, REPLACE_ITEMS, etc.) |
| Actions History UI  | actions_history_window.cpp     | vis_layer/ui/docks/actions_history.py| ✅    | `ActionsHistoryDock` with undo stack display (86 lines) |
| MapCanvasWidget     | map_canvas.cpp                 | vis_layer/ui/canvas/widget.py     | ✅       | Event-driven rendering + input coalescing (ARCHITECTURE.md parity) |
| OpenGL Renderer     | map_drawer.cpp                 | vis_layer/renderer/opengl_canvas.py| ✅      | Backend + batching + event-driven refresh; OpenGLCanvasWidget is now the main canvas |
| In-Game Preview     | ingame_preview.cpp (legacy)     | vis_layer/preview/, logic_layer/sprite_system/ | ⚠️ | Pygame preview window + legacy dat reader + threading (2026-01-30) |
| Sprite Manager      | graphic_manager.cpp            | core/assets/sprite_appearances.py | ⚠️       | Partial, see [ANALISE_PY_RME_CANARY_2025.md](ANALISE_PY_RME_CANARY_2025.md) |
| DrawingOptions      | drawing_options.cpp            | logic_layer/drawing_options.py     | ✅       | Coordinator in `vis_layer/renderer/drawing_options_coordinator.py` |
| Live Server/Client  | live_server.cpp, live_client.cpp| core/protocols/live_server.py, live_client.py| ⚠️ | Login payload encoding + TILE_UPDATE broadcast; state sync pending |
| Map IO (OTBM)       | iomap_otbm.cpp                 | core/io/otbm/                     | ✅       |             |
| Map IO (OTMM)       | iomap_otmm.cpp                 | core/io/otmm.py                   | ✅       | Loader/saver + roundtrip tests |
| Minimap             | iominimap.cpp, minimap_window.cpp| vis_layer/ui/docks/minimap.py    | ✅       | Dock widget + PNG export in tools/minimap_export.py |
| Assets Loader       | client_assets.cpp              | core/assets/                      | ✅       | Full support: modern (catalog-content.json + appearances.dat) and legacy (Tibia.dat/.spr); see `asset_profile.py`, `loader.py` |
| Asset Profile       | N/A                            | core/assets/asset_profile.py      | ✅       | Auto-detect modern vs legacy assets; conflict detection |
| Legacy DAT/SPR      | dat_spr_loader.cpp             | core/assets/legacy_dat_spr.py     | ✅       | RLE sprite decode, LRU cache, memory guard integration |
| Appearances DAT     | appearances.pb                 | core/assets/appearances_dat.py    | ✅       | Protobuf parser, SpriteAnimation, phase selection by time_ms |
| Animation Clock     | map_display.cpp                | vis_layer/ui/main_window/editor.py| ✅       | `animation_time_ms()` + `advance_animation_clock()` for animated sprites |
| Selection/Clipboard | selection.cpp, copybuffer.cpp  | logic_layer/session/selection.py, clipboard.py| ✅ |             |
| Updater             | updater.cpp                    | tools/updater.py                  | ❌       |             |
| PNG Export/Import   | pngfiles.cpp                   | tools/pngfiles.py                 | ❌       |             |
| Random Utils        | mt_rand.cpp                    | core/utils/random.py              | ⚠️       | Partial, see [ANALISE_PY_RME_CANARY_2025.md](ANALISE_PY_RME_CANARY_2025.md) |
| Map Validator       | map.cpp (validation)           | core/io/map_validator.py          | ✅       | Full validation: tiles, houses, zones, spawns, waypoints, towns |
| Properties Panel    | properties_window.cpp          | vis_layer/ui/docks/properties_panel.py| ✅   | Tile/Item/House/Spawn/Waypoint/Zone inspection |
| Find Item Dialog    | find_item_window.cpp           | vis_layer/ui/main_window/dialogs.py (FindItemDialog)| ✅ | Search items by server ID |
| Find Entity Dialog  | find_item_window.cpp           | vis_layer/ui/main_window/dialogs.py (FindEntityDialog)| ✅ | Item/Creature/House tabs |
| Replace Items Dialog| replace_items_window.cpp       | vis_layer/ui/main_window/dialogs.py (ReplaceItemsDialog)| ✅ | From/To server ID replacement |
| Find Positions Dialog| N/A                           | vis_layer/ui/main_window/dialogs.py (FindPositionsDialog)| ✅ | Results list with positions |
| Waypoint Query Dialog| N/A                          | vis_layer/ui/main_window/dialogs.py (WaypointQueryDialog)| ✅ | Search waypoints by name |
| Find Named Positions | N/A                           | vis_layer/ui/main_window/dialogs.py (FindNamedPositionsDialog)| ✅ | Show list of named positions (waypoints, houses, etc.) |
| Map Statistics Dialog| N/A                           | vis_layer/ui/main_window/dialogs.py (MapStatisticsDialog)| ✅ | Display and export map statistics (62 lines) |
| Take Screenshot     | N/A (different approach)       | vis_layer/ui/main_window/qt_map_editor_view.py (_take_screenshot)| ✅ | F10 shortcut, PNG export via QPixmap |
| Preferences Window  | preferences.cpp (735 lines)    | vis_layer/ui/main_window/preferences_dialog.py | ✅ | Settings dialog with tabs: General, Editor, Graphics, UI, Client Folder. 5 tabs implemented with full UI (2026-01-23) |
| Add Item Window     | add_item_window.cpp (153 lines)| vis_layer/ui/main_window/add_item_dialog.py | ✅ | Dialog for adding items to tilesets by server ID. Includes item info display and tileset selection (2026-01-23) |
| Browse Tile Window  | browse_tile_window.cpp (312 lines) | vis_layer/ui/main_window/browse_tile_dialog.py | ✅ | Browse and manage items on a selected tile. List view with remove/properties actions (2026-01-23) |
| Container Properties| container_properties_window.cpp | vis_layer/ui/main_window/container_properties_dialog.py | ✅ | Edit container item properties. Add/remove items from containers (2026-01-23) |
| Import Map Dialog   | iomap.cpp (import functions)   | vis_layer/ui/main_window/import_map_dialog.py | ✅ | Import another map with X/Y/Z offset, merge modes, and selective import (tiles/houses/spawns/zones) (2026-01-23) |
| Selection Operations | N/A (new feature)             | logic_layer/operations/selection_operations.py | ✅ | Search/count/remove duplicates within selection. Includes `search_items_in_selection()`, `count_monsters_in_selection()`, `remove_duplicates_in_selection()` (2026-01-28) |
| Find Creature Dialog | find_item_window.cpp          | vis_layer/ui/main_window/find_item.py + dialogs.py | ✅ | Search creatures (monsters/NPCs) by name. Supports item/creature/house modes (VERIFIED 2026-01-28) |
| Brush Size Preview  | N/A                           | vis_layer/ui/panels/brush_size_panel.py | ✅ | Visual preview of brush size/shape (BrushSizePreview widget) (VERIFIED 2026-01-28) |
| Paste Preview Overlay | N/A                         | vis_layer/ui/overlays/paste_preview.py | ✅ | Semi-transparent preview of paste operation (PastePreviewOverlay) (VERIFIED 2026-01-28) |

---

## 🧩 High-Priority TODOs

- [ ] Port all missing brushes and advanced brush features
- [x] Integrate MapDrawer into the main canvas (QPainter backend)
- [x] Implement OpenGL backend for MapDrawer (tile sprites + batching)
- [x] Implement unified asset loader (modern + legacy Tibia clients)
- [x] Implement appearances.dat parser with animation support
- [ ] Implement full live server/client protocols (state sync pending)
- [ ] Finish NetworkedActionQueue for live mode
- [ ] Remove all stubs and partials in logic_layer/ and vis_layer/
- [ ] Validate all ported features against legacy C++ for 1:1 behavior

---

## 🔗 Deep-Dive Analysis & Context

- [ANALISE_FALTANTE.md](ANALISE_FALTANTE.md): Full comparative analysis, feature-by-feature
- [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md): Detailed parity notes and technical context
- [IMPLEMENTATION_TODO.md](IMPLEMENTATION_TODO.md): Professional TODOs and stub tracking
- [TODO_EXPENSIVE.md](TODO_EXPENSIVE.md): High-priority technical debt and parity
- [WALKTHROUGH.md](WALKTHROUGH.md): Modernization phases and parity verification

---

## 📝 Notes for Agents & Contributors

- Always cross-reference legacy C++ files for acceptance criteria
- Document all ported features with tests and references
- Use status icons and keep this checklist up to date
- For ambiguous cases, consult deep-dive docs above

---

End of master checklist.
