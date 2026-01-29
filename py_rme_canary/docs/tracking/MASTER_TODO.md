# MASTER TODO - py_rme_canary

**Generated:** 2026-01-27
**Source:** Aggregation of `GAP_ANALYSIS.md`, `features.md`, `ANALISE_FALTANTE.md`, and `IMPLEMENTATION_STATUS.md`.

> **Status Key:**
> - [ ] Pending
> - [/] In Progress
> - [x] Completed (Included for context if recently done)

---

## 🚨 P0: Critical / Core Architecture

### 🔄 Map Format Conversion & IDs
From `features.md`:
- [x] **Map Format Conversion:** Convert entire maps between ServerID (OTBM 1-4) and ClientID (OTBM 5/6) formats (includes ClientID loader/saver and menu action).
- [x] **Technical:** Verify `ItemIdMapper` full bidirectional mapping for all client versions.

### 🌐 Live Protocol (Collaboration)
From `IMPLEMENTATION_STATUS.md` & `ANALISE_FALTANTE.md`:
- [x] **State Synchronization:** Full map state sync upon join.
- [x] **Networked Action Queue:** Broadcast undo/redo and complex actions.
- [x] **Cursor Broadcasting:** Show other users' mouse cursors.
- [x] **Chat Interface:** Basic chat for connected peers.
- [x] **Kick/Ban:** Host controls.

### 🎥 Rendering & Assets
- [x] **Live Preview:** Real-time brush preview (2026-01-28: canvas integration with overlays).
- [x] **Dragging Shadow:** Visual feedback when dragging selections (2026-01-28: `vis_layer/ui/overlays/drag_shadow.py`, 9/9 tests passing).
    - [x] **Lighting:** Complete light rendering (2026-01-29: ambient overlay + per-tile glow & strength labels via LightSettings).
- [ ] **Performance (RME - C:\Users\Marcelo Henrique\Desktop\projec_rme\RME):** Investigate OpenGL 4.5 techniques (Branch: `sentinel-opengl-modernization`, `fixer-core-optimization`).
- [ ] **Memory Optimization (RME - C:\Users\Marcelo Henrique\Desktop\projec_rme\RME):** Investigate `keeper-live-memory` for live memory management.
- [ ] **Lighting (RME - C:\Users\Marcelo Henrique\Desktop\projec_rme\RME):** Investigate "Better light system" logic from fork.
- [ ] **Minimap (RME - C:\Users\Marcelo Henrique\Desktop\projec_rme\RME):** Investigate "Fixed minimap lag" (Branch: `opengl-optimization-minimap`).
- [ ] **Brushes (RME - C:\Users\Marcelo Henrique\Desktop\projec_rme\RME):** Check `brushes` branch for new brush types or logic.

---

## 🛠️ P1: Essential Features (v2.0 Goals)

### 🖱️ Advanced Selection & Operations
From `ANALISE_FALTANTE.md`:
- [x] **Search on Selection:** Search items only within selected area (2026-01-28: `search_items_in_selection()` in logic_layer/operations/selection_operations.py).
- [x] **Remove on Selection:** Remove items only within selected area (already exists via `remove_items_in_map(selection_only=True)`).
- [x] **Count Monsters:** Count entities in selection (2026-01-28: `count_monsters_in_selection()` in logic_layer/operations/selection_operations.py).
- [x] **Remove Duplicates:** specific tool for cleaning duplicates in selection (2026-01-28: `remove_duplicates_in_selection()` in logic_layer/operations/selection_operations.py).
- [x] **Find Creature:** Dedicated dialog/tab to find specific spawn instances (VERIFIED 2026-01-28: Already exists in vis_layer/ui/main_window/find_item.py and dialogs.py with creature search mode).

### 📋 Clipboard & Cross-Version
From `features.md`:
- [x] **Cross-Version Copy/Paste:** Logic to translate IDs during paste between instances/versions (2026-01-28: `logic_layer/cross_version/clipboard.py`, 8/8 tests passing).
- [x] **Sprite Hash Matching:** Fallback for copy/paste when IDs don't match (FNV-1a) (2026-01-28: `logic_layer/cross_version/sprite_hash.py`, 10/10 tests passing).
- [x] **Multiple Instances:** Run several independent editor instances (different SPR/DAT) (2026-01-28: New Instance window action).
- [x] **Instance Transfer:** Transfer Creatures/Spawns between instances via clipboard (2026-01-28: clipboard serialization + session import).
- [x] **Auto-Correction:** Automatically find correct ServerID if sprite hash matches but ID is wrong (2026-01-28: `logic_layer/cross_version/auto_correction.py`, 11/11 tests passing).

### ⚙️ Preferences & Config
- [x] **Shortcuts Editor:** Keyboard shortcuts configuration with 10+ custom hotkeys, position hotkeys, conflict detection (2026-01-28: `logic_layer/settings/shortcuts.py`, 22/22 tests passing).
- [x] **Grid Settings:** Configurable grid color/transparency (2026-01-28: `logic_layer/settings/grid_settings.py`, 19/19 tests passing).
- [x] **Light Settings:** Global ambient light configuration (2026-01-28: `logic_layer/settings/light_settings.py`, 23/23 tests passing).
- [ ] **Palette UX (RME  - C:\Users\Marcelo Henrique\Desktop\projec_rme\RME):** Investigate improvements from `palette-ux-improvements` branch (better tooltips, layout).
- [ ] **Palette UX (RME - C:\Users\Marcelo Henrique\Desktop\projec_rme\RME):** Investigate improvements from `palette-ux-improvements` branch (better tooltips, layout).
- [ ] **Modern UI (RME - C:\Users\Marcelo Henrique\Desktop\projec_rme\RME):** Investigate `designer-modernize-ui` branch.
- [x] **Doodad Brush Logic:** Implement "Erase Like" (erase only same brush items) functionality in `TransactionalBrush` (2026-01-29).
    - *Context:* RME `doodad_brush.cpp` supports erasing only items owned by the current doodad brush; Python now matches erase-like + unique-item protection.
- [x] **Brush Data Parity:** Verify `TableBrushSpec` and `CarpetBrushSpec` load correctly from materials XML in all cases (2026-01-29: chance defaults, warnings, local-id fallback parity + tests).

---

## 🚀 P2: Advanced UI & Tools

### 🧙‍♂️ Map Generation / Templates
From `ANALISE_FALTANTE.md` ("Completely Faltante"):
- [ ] **Templates System:** Generate new maps from presets (7.4, 8.6, etc.).
- [ ] **Tileset Manager:** UI to create/edit custom tilesets.
- [x] **Welcome Dialog:** "New/Open/Recent" splash screen (2026-01-28).

### 📤 Import/Export
- [x] **BMP Support:** Export map/minimap to BMP (2026-01-28).
- [x] **Import Map (Offset):** Import map files with offset and merge options (2026-01-28).
- [x] **Import Monsters/NPCs:** Import from XML/Lua folder recursively (2026-01-28: `logic_layer/operations/import_creatures.py`, 8/8 tests passing).

### 📊 Statistics
- [ ] **Graphs:** Visual representation of map stats.
- [x] **Export Stats:** Save statistics to XML/CSV/JSON (2026-01-28: `logic_layer/operations/export_statistics.py`, 12/12 tests passing).
- [ ] **Logging (RME - C:\Users\Marcelo Henrique\Desktop\projec_rme\RME):** Investigate `instrument-logging` for performance metrics.

---

## 🧹 P3: Cleanup & Refactoring

- [ ] **Remove Legacy Stubs:** Final sweep of `logic_layer` and `vis_layer` for any unused files.
- [x] **Standardize Tests:** Ensure all tests follow `test_*.py` pattern (2026-01-29: audit complete; no nonconforming test files found).
- [ ] **Documentation:** Update `WALKTHROUGH.md` with final v2.0 workflow.

---

## 🔮 P4: Future / v4.0 (In-Game Preview)

### 📋 Fase 1: Preparação e Estrutura Base
*(Ref: C:\Users\Marcelo Henrique\Desktop\projec_rme\RME`)* Structure
- [x] **Client Files:** Obtain `.spr` and `.dat`, create `client_files/` directory.
- [x] **Format Research:** Study `.dat` (flags, dimensions) and `.spr` (compression, caching) formats.
- [x] **Directory Structure:** Create `logic_layer/sprite_system/`, `vis_layer/preview/`, `tests/preview_tests/`.

### 🔧 Phase 2: Sprite Loader (.spr & .dat)
- [x] **.dat Reader:** Implement header, flags, dimensions, pattern reading (metadata dictionary).
- [x] **.spr Reader:** Implement header, pointer table, RLE decoding, pixel conversion (RGBA).
- [x] **Cache System:** Implement LRU cache with memory limits (MemoryGuard integration).
- [x] **Validation:** Compare loaded sprites with original client (transparent transparency, multi-tile).

### 🎨 Phase 3: In-Game Renderer
- [x] **Rendering Order:** Implement correct layer stacking (Ground → Bottom → Top).
- [x] **Isometric Perspective:** Implement World → Screen coordinate conversion (32x32 tiles).
- [x] **Multi-Sprite Items:** Render 2x2, 3x3 items with correct offsets.
- [x] **Animations:** Implement frame counting, delta_time updates, animation speed (200ms default).
- [x] **Stackable Items:** Render counts for stackable items (text with shadow).

### 🪟 Phase 4: Preview Window
- [x] **Window Creation:** Pygame window ("In-Game Preview - RME"), resizeable.
- [x] **Render Loop:** Main loop (60 FPS), event processing, display update.
- [x] **Synchronization:** Sync camera with editor, update on map changes.
- [x] **Viewport:** Culling (render only visible tiles), support zoom/pan.

### ⚙️ Phase 5: Advanced Features
- [ ] **Optional Grid:** Toggleable grid overlay (Key 'G').
- [ ] **HUD:** Show FPS, Camera Position, Sync Status.
- [ ] **Lighting (Optional):** Light intensity per tile, ambient light (day/night).
- [ ] **Creatures (Optional):** Render creature sprites/outfits with direction.

### 🔗 Phase 6: Editor Integration
- [x] **Actions:** New `toggle_preview` action, F5 shortcut.
- [x] **Menu:** "In-Game Preview" item in View menu.
- [x] **Threading:** Daemon thread/process for preview window to avoid blocking editor.
- [x] **Communication:** Message queue for Editor → Preview updates.

### 🧪 Phase 7: Testing & Validation
- [x] **Unit Tests:** Loaders (.dat/.spr), cache, coordinate conversion.
- [ ] **Integration Tests:** Preview sync, item add/remove updates.
- [ ] **Performance Tests:** FPS measurements (small vs large viewport), memory usage.
- [ ] **Visual Tests:** Compare with real client side-by-side.

### 🐛 Phase 8: Debug & Polish
- [ ] **Logging:** Sprite loading, rendering errors.
- [ ] **Error Handling:** Missing sprites (placeholders), invalid IDs.
- [ ] **Optimization:** Profiling, dirty rectangles, sprite batching.
- [ ] **Polish:** Loading feedback, quality options, transitions.

