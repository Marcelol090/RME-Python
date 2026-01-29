# Legacy GUI → py_rme_canary (status)

Este documento mapeia funcionalidades observadas na GUI legado (C++/wxWidgets) para o que existe/é viável no editor Python.

## Observado no legado (C++)

Fontes principais:
- `source/gui_ids.h`: enumera modos, shapes e IDs.
- `source/main_menubar.cpp`: ações de menu (Undo/Redo, Automagic, etc.).
- `source/main_toolbar.cpp`: toolbars (New/Open/Save, sizes, position, indicators).
- `source/map_display.cpp` + `getTilesToDraw`: regra de brush size/shape e área de “tiles to border”.

### Editor / Input
- Brush shape: `BRUSHSHAPE_SQUARE` / `BRUSHSHAPE_CIRCLE`.
- Brush size: 0..7 (e tamanhos predefinidos em palette/toolbar).
- `USE_AUTOMAGIC`: toggle para auto-border/wallize pós-draw.
- `Go To Position`: campos X/Y/Z + botão.
- Seleção vs Desenho (`SELECTION_MODE`, `DRAWING_MODE`).
- Replace (ground): Alt-clique inicia replace mode.
- Flood fill (ground): `Ctrl+D` com fill em `getTilesToDraw(..., fill=true)`.

### Menus/Toolbars (amostra)
- File: New/Open/Save/Save As.
- Edit: Undo/Redo; Cut/Copy/Paste (depende de seleção/copybuffer).
- View: Zoom in/out/normal; toggles de grid, sombras, minimap, overlays.
- Tools: Borderize selection/map; randomize selection/map; border builder.

## Implementado no Python (Tk UI)

Arquivo: `py_rme_canary/vis_layer/tk_app.py`

- File: New/Open/Save/Save As (OTBM via `core.io`).
- Edit: Undo/Redo (via `EditorSession`).
- View: Zoom in/out (tile size) + pan.
- Floor (Z): entrada manual.

## Paridade planejada (curto prazo)

Fácil e suportado pelo backend atual:
- `Automagic` toggle (habilitar/desabilitar auto-border na finalização do stroke).
- Brush size + shape (square/circle) replicando `getTilesToDraw` (sem seleção).
- Lista/pesquisa de brushes (de `data/brushes.json`).
- Go To Position (viewport origin X/Y e floor Z).

Requer backend novo/maior:
- Selection mode + Cut/Copy/Paste/duplicate/delete selection.
- Minimap real + overlays (grid/light/houses/pathing/etc.).
- Replace tool (ground) por “target brush” capturado do tile.
- Flood fill real (ground) respeitando regras de bloqueio e áreas.
- Brushes especiais (PZ/NOPVP/NOLOGOUT/PVPZONE, doors, hooks/pickupables/etc.).

---

## C++ Source Mapping (Pending Port)

> Consolidated from `missing_implementation.md`

### Networking / Live
- source/live_client.cpp -> py_rme_canary/core/protocols/live_client.py (High)
- source/live_server.cpp -> py_rme_canary/core/protocols/live_server.py (High)
- source/live_peer.cpp -> py_rme_canary/core/protocols/live_peer.py (High)
- source/live_socket.cpp -> py_rme_canary/core/protocols/socket.py (High)
- source/live_action.cpp, source/live_packets.h -> py_rme_canary/core/protocols/messages.py (High)
- source/rme_net.cpp, source/net_connection.cpp -> py_rme_canary/core/protocols/net_connection.py (High)
- source/process_com.cpp -> py_rme_canary/core/protocols/process_com.py (Medium)

### UI — Janelas e diálogos
- source/about_window.cpp / about_window.h -> vis_layer/ui/dialogs.py or vis_layer/ui/about.py (Low)
- source/add_item_window.cpp -> vis_layer/ui/main_window/add_item.py (Medium)
- source/add_tileset_window.cpp -> vis_layer/ui/main_window/add_tileset.py (Medium)
- source/tileset_window.cpp, source/tileset.cpp -> vis_layer/ui/tileset.py (Medium)
- source/find_item_window.cpp -> vis_layer/ui/main_window/find_item.py (verify features) (Medium)
- source/find_creature_window.cpp -> vis_layer/ui/main_window/find_creature.py (Medium)
- source/container_properties_window.cpp -> vis_layer/ui/container_properties.py (Medium)
- source/properties_window.cpp -> vis_layer/ui/properties.py (Medium)
- source/preferences.cpp -> vis_layer/ui/preferences.py or core/config (Low)
- source/main_menubar.cpp -> vis_layer/ui/main_window/build_menus.py (Low/Medium)
- source/main_toolbar.cpp -> vis_layer/ui/main_window/qt_map_editor_toolbars.py (Low/Medium)

### Paletas / Widgets legadas
- source/palette_window.cpp -> vis_layer/ui/docks/palette.py (Medium)
- source/palette_waypoints.cpp, palette_npc.cpp, palette_monster.cpp, palette_house.cpp, palette_brushlist.cpp, palette_common.cpp, palette_zones.cpp -> vis_layer/ui/docks/* (verify filters / grouping / dragdrop) (Medium)

### Map drawing / Render
- source/map_drawer.cpp -> vis_layer/renderer/* (port algorithms; heavy parts may remain C++) (Medium)
- source/map_display.cpp -> vis_layer/renderer/display.py (Medium)
- source/light_drawer.cpp -> vis_layer/renderer/light.py (Low/Medium)
- source/iominimap.cpp, source/minimap_window.cpp -> vis_layer/ui/docks/minimap.py (Low)

### Brushes / Tools (UI & logic)
- source/house_brush.cpp, house_exit_brush.cpp -> logic_layer/brushes/house_brush.py (if not covered) (Medium)
- source/monster_brush.cpp, npc_brush.cpp, spawn_monster_brush.cpp, spawn_npc_brush.cpp -> logic_layer/brushes/* or logic_layer/session tools (Medium)
- source/doodad_brush.cpp -> logic_layer/brush_definitions.py (doodad_spec exists; verify parity) (Medium)

### IO / Map formats / Conversion
- source/iomap_otbm.cpp, iomap_otbm.h -> core/io/otbm (exists) — verify full parity (High)
- source/iomap_otmm.cpp, iomap_otmm.h (OTMM conversion) -> core/io/otmm.py or tools/otmm_converter.py (Medium)
- source/pngfiles.cpp -> tools/pngfiles.py or vis_layer/renderer helpers (Low)

### Assets / Tilesets
- source/client_assets.cpp, client_assets.h -> core/assets or vis_layer asset loaders (Medium)
- Tileset UI & import/export: see tileset files above (Medium)

### Selection / Clipboard / History
- source/selection.cpp, selection.h -> logic_layer/session/selection.py (partial) (Medium)
- source/copybuffer.cpp, copybuffer.h -> logic_layer/session/clipboard.py (exists; verify parity) (Medium)

### Utilities / Misc
- source/updater.cpp -> tools/updater.py (Low)
- source/pngfiles.cpp -> tools/pngfiles.py (Low)
- source/mt_rand.cpp -> core/utils/random.py or use Python's random (Low)

### Areas já cobertas / revisar (pode estar parcial)
- Brushes & auto-border: logic_layer/brush_definitions.py, auto_border.py, brush_factory.py, brushes.py — confirmar que todas as regras de brush_tables.cpp / brush_enums.h foram migradas.
- Core IO: core/io/otbm/* — confirm full feature parity com iomap_otbm.cpp (trees, attributes, streaming edge-cases).
- Spawns / criaturas: core/io/spawn_xml.py, core/io/creatures_xml.py — confirm comportamento equivalente a spawn_monster.cpp / spawn_npc.cpp (UI vs data model).
