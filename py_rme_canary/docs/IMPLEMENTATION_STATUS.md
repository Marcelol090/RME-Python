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

| Area                | Legacy C++/Lua File(s)         | Python Destination                | Status   | Notes/Links |
|---------------------|-------------------------------|-----------------------------------|----------|-------------|
| Brushes (core)      | brush.cpp, ground_brush.cpp   | logic_layer/brush_definitions.py  | ✅       | Full MVP, see TODO for advanced |
| WallBrush           | wall_brush.cpp                | logic_layer/brush_definitions.py  | ✅       |             |
| Auto-border         | auto_border.cpp               | logic_layer/auto_border.py        | ✅       |             |
| BrushManager        | brush_manager.cpp             | logic_layer/brush_definitions.py  | ✅       |             |
| TableBrush          | table_brush.cpp               | logic_layer/brush_definitions.py  | ⚠️       | MVP implemented; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| CarpetBrush         | carpet_brush.cpp              | logic_layer/brush_definitions.py  | ⚠️       | MVP implemented; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| DoorBrush           | door_brush.cpp                | logic_layer/brush_definitions.py  | ⚠️       | MVP/virtual tooling; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| DoodadBrush         | doodad_brush.cpp              | logic_layer/brush_definitions.py  | ⚠️       | MVP+ implemented; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| HouseBrush          | house_brush.cpp               | logic_layer/brushes/house_brush.py| ⚠️       | MVP/virtual (metadata-only); see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| HouseExitBrush      | house_exit_brush.cpp          | logic_layer/brushes/house_brush.py| ⚠️       | MVP/virtual; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| WaypointBrush       | waypoint_brush.cpp            | logic_layer/brushes/waypoint_brush.py| ⚠️   | MVP/virtual; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| Monster/NpcBrush    | monster_brush.cpp, npc_brush.cpp| logic_layer/brushes/monster_brush.py| ⚠️   | MVP tools + smear; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| SpawnMonster/Npc    | spawn_monster_brush.cpp, spawn_npc_brush.cpp| logic_layer/brushes/spawn_brush.py| ⚠️ | MVP tools + smear; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| FlagBrush           | flag_brush.cpp                | logic_layer/brushes/flag_brush.py | ⚠️       | Virtual (metadata-only); see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| ZoneBrush           | zone_brush.cpp                | logic_layer/brushes/zone_brush.py | ⚠️       | Virtual (metadata-only); see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| OptionalBorderBrush | optional_border_brush.cpp     | logic_layer/brushes/optional_border_brush.py| ⚠️ | MVP/virtual; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| EraserBrush         | eraser_brush.cpp              | logic_layer/brushes/eraser_brush.py| ⚠️     | MVP; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| Recent Brushes      | palette_window.cpp            | vis_layer/ui/docks/palette.py     | ⚠️       | MVP implemented; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| Brush Shapes/Size   | map_display.cpp               | logic_layer/brush_definitions.py  | ⚠️       | Implemented (legacy footprint); see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| Brush Variation     | brush.cpp                     | logic_layer/brush_definitions.py  | ⚠️       | MVP implemented; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| Brush Thickness     | brush.cpp                     | logic_layer/brush_definitions.py  | ⚠️       | MVP implemented; see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| Drag/Smear          | brush.cpp                     | logic_layer/brush_definitions.py  | ⚠️       | Partial (select tools); see [TECHNOLOGY_IMPLEMENTATION_DETAILS.md](TECHNOLOGY_IMPLEMENTATION_DETAILS.md) |
| Border Builder      | border_builder.cpp             | logic_layer/auto_border.py        | ❌       |             |
| Border Groups       | border_groups.cpp              | logic_layer/auto_border.py        | ❌       |             |
| Border Friends/Hate | border_friends.cpp             | logic_layer/auto_border.py        | ❌       |             |
| Ground Equivalents  | ground_equivalents.cpp         | logic_layer/auto_border.py        | ❌       |             |
| EditorSession       | editor_session.cpp             | logic_layer/editor_session.py     | ✅       |             |
| Selection Modes     | selection.cpp                  | logic_layer/session/selection.py  | ⚠️       | Partial, see [ANALISE_FALTANTE.md](ANALISE_FALTANTE.md) |
| Clipboard           | copybuffer.cpp                 | logic_layer/session/clipboard.py  | ✅       |             |
| Undo/Redo           | action.cpp                     | logic_layer/history/action.py     | ✅       |             |
| Mouse Gestures      | gestures.cpp                   | logic_layer/session/gestures.py   | ✅       |             |
| Move Selection      | selection.cpp                  | logic_layer/session/move.py       | ✅       |             |
| Borderize Selection | borderize.cpp                  | logic_layer/operations/borderize.py| ❌     |             |
| Randomize Selection | randomize.cpp                  | logic_layer/operations/randomize.py| ❌     |             |
| Clear Selection     | selection.cpp                  | logic_layer/session/selection.py  | ⚠️       | Partial, see [ANALISE_FALTANTE.md](ANALISE_FALTANTE.md) |
| ActionQueue         | action_queue.cpp               | logic_layer/history/manager.py    | ⚠️       | Partial, see [IMPLEMENTATION_TODO.md](IMPLEMENTATION_TODO.md) |
| NetworkedActionQueue| live_action.cpp                | core/protocols/action_queue.py    | ❌       |             |
| Action Types        | action_types.cpp               | logic_layer/history/action.py     | ⚠️       | Partial, see [IMPLEMENTATION_TODO.md](IMPLEMENTATION_TODO.md) |
| MapCanvasWidget     | map_canvas.cpp                 | vis_layer/ui/canvas/widget.py     | ✅       | Event-driven rendering + input coalescing (ARCHITECTURE.md parity) |
| OpenGL Renderer     | map_drawer.cpp                 | vis_layer/renderer/opengl_canvas.py| ⚠️      | Backend + batching + event-driven refresh; OpenGLCanvasWidget is now the main canvas |
| Sprite Manager      | graphic_manager.cpp            | core/assets/sprite_appearances.py | ⚠️       | Partial, see [ANALISE_PY_RME_CANARY_2025.md](ANALISE_PY_RME_CANARY_2025.md) |
| DrawingOptions      | drawing_options.cpp            | logic_layer/drawing_options.py     | ✅       | Coordinator in `vis_layer/renderer/drawing_options_coordinator.py` |
| Live Server/Client  | live_server.cpp, live_client.cpp| core/protocols/live_server.py, live_client.py| ⚠️ | Base LiveSocket/LivePeer + TILE_UPDATE broadcast; more protocols pending |
| Map IO (OTBM)       | iomap_otbm.cpp                 | core/io/otbm/                     | ✅       |             |
| Map IO (OTMM)       | iomap_otmm.cpp                 | core/io/otmm.py                   | ✅       | Loader/saver + roundtrip tests |
| Minimap             | iominimap.cpp, minimap_window.cpp| vis_layer/ui/docks/minimap.py    | ❌       |             |
| Assets Loader       | client_assets.cpp              | core/assets/                      | ⚠️       | Partial, see [ANALISE_PY_RME_CANARY_2025.md](ANALISE_PY_RME_CANARY_2025.md) |
| Selection/Clipboard | selection.cpp, copybuffer.cpp  | logic_layer/session/selection.py, clipboard.py| ✅ |             |
| Updater             | updater.cpp                    | tools/updater.py                  | ❌       |             |
| PNG Export/Import   | pngfiles.cpp                   | tools/pngfiles.py                 | ❌       |             |
| Random Utils        | mt_rand.cpp                    | core/utils/random.py              | ⚠️       | Partial, see [ANALISE_PY_RME_CANARY_2025.md](ANALISE_PY_RME_CANARY_2025.md) |

---

## 🧩 High-Priority TODOs

- [ ] Port all missing brushes and advanced brush features
- [x] Integrate MapDrawer into the main canvas (QPainter backend)
- [x] Implement OpenGL backend for MapDrawer (tile sprites + batching)
- [ ] Implement full live server/client protocols
- [ ] Finish minimap and assets loader parity
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
