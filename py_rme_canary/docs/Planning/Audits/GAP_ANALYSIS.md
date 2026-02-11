# RME Gap Analysis & Priority Big TODO

## 1. Executive Summary & Analysis

**Analyzed Artifacts:**
- **Legacy:** `Remeres-map-editor-linux-4.0.0` (v3.9.15) - Validated Production-Ready Linux Port.
- **Python:** `py_rme_canary` (2026-01) - Modern Python port using PyQt6.
- **Docs:** `ANALISE_FALTANTE.md`, `IMPLEMENTATION_STATUS.md`, `sonnet_workflow.md`.

### Architectural Alignment
The legacy project (v3.9.15) emphasizes an **Event-Driven Rendering** architecture (No continuous render loop, `OnPaint` only on dirtiness) to solve Linux input flooding.
- **Verdict:** `py_rme_canary` **successfully adopts this architecture**. `MapCanvasWidget` relies on signals (`_on_tiles_changed`) and QPaintEvents, avoiding a busy loop. The OpenGL backend implementation aligns with the legacy's performance optimizations.

### Core Gaps
While the "Skeleton" (Core IO, Rendering, Basic Editing) is feature-complete, the "Flesh" (Specialized Tools, Complex Dialogs, nuanced Interaction) has significant gaps.
- **Status Update (2026-02-10):** BorderBuilder custom-rule authoring parity with legacy `borders.xml` is completed (UI editor + import/export + runtime overrides persistence).
- **Status Update (2026-02-10):** strict QA closure is completed (`mypy --strict` clean on full project), with remaining work focused on incremental UX parity refinements.

---

## 2. THE BIG PRIORITY TODO (Road to Parity)

This list is prioritized: **P0 (Blockers)** -> **P1 (Core UX)** -> **P2 (Advanced)** -> **P3 (Cleanup)**.

### 🚨 P0: Critical Editing Tools (The "Broken" Workflow)
*Without these, the editor is functionally limited compared to Legacy.*

- [x] **Implement Missing Specialized Brushes:**
    - Reference: `source/house_brush.cpp`, `source/spawn_brush.cpp`, `source/waypoint_brush.cpp`
    - **Task:** Create real Logic implementations in `logic_layer/brushes/` for:
        - [x] `HouseBrush`: Handle house tiles, IDs, and ownership.
        - [x] `HouseExitBrush`: Special logic for verifying door/house connectivity.
        - [x] `WaypointBrush`: Navigation points editing.
        - [x] `SpawnMonsterBrush` / `SpawnNpcBrush`: Spawn radius and time logic.
        - [x] `OptionalBorderBrush`: For forced auto-bordering.
- [x] **Fix Selection Modes:**
    - Reference: `source/selection.cpp`
    - **Task:** Implement defining logic for selection depth:
        - [x] `SELECT_MODE_COMPENSATE` (Legacy default: Auto-selects intuitive volume)
        - [x] `SELECT_MODE_CURRENT` (Current Z only)
        - [x] `SELECT_MODE_LOWER` (Current + Lower Zs)
        - [x] `SELECT_MODE_VISIBLE` (All visible Zs)
- [x] **Completeness of Auto-Bordering:**
    - ~~**Task:** Finalize `BorderBuilder` UI or logic to allow custom border rules matching Legacy's `borders.xml` flexibility.~~ ✅ Done — Full import/export/editor with `borders_xml_io.py` + `BorderBuilderDialog` + overrides persistence.

### 🛠️ P1: Essential UI & Dialogs (The User Experience)
*Legacy RME relies heavily on these dialogs for map management.*

- [x] **Properties Window (Complex Items):**
    - Reference: `source/properties_window.cpp`
    - **Task:** Implement `PropertiesDialog` that adapts content based on selection:
        - [x] **Tile:** Edit Ground, Flags (PZ, No Logout, etc).
        - [x] **Item:** Edit count, ActionID, UniqueID, Destination (Teleports).
        - [x] **House:** Edit Name, Rent, Guild limits.
        - [x] **Spawn:** Edit Radius, Spawn Time.
        - [x] **Container:** Edit child items (recursively?).
- [x] **Map Management Dialogs:**
    - [x] **Map Properties:** Dimensions, descriptions, OTBM header data.
    - [x] **Town Editor:** Manage Town IDs, Names, Temple positions.
- [x] **Search & Replace UI:**
    - [x] **Search Results Dock:** Persistent list of search results (clickable to jump).
    - [x] **Advanced Replace:** "Replace in Selection" vs "Replace in Map".

### 🚀 P2: Advanced Features & Live Mode
*High value differentiation, but not strictly modifying the map data structure.*

- [x] **Live Collaboration (Real-Time):**
    - Reference: `source/live_server.cpp`, `source/live_client.cpp`
    - **Task:** Finish the `NetworkedActionQueue`.
        - [x] State Synchronization (Initial map sync).
        - [x] Cursor Broadcasting (See other users' mouse).
        - [x] Chat/Log Interface.
- [x] **Minimap Nav & Export:**
    - [x] **Interactive Minimap:** Click to navigate (currently basic).
    - [x] **Full Export:** Export huge maps to PNG (tiled if necessary).

### 🧹 P3: Technical Debt & Verification
*Ensuring long-term maintainability.*

- [x] **Cleanup `data_layer/`:**
    - **Task:** Delete the `py_rme_canary/data_layer/` directory. It is a legacy artifact duplicating `core/`.
- [x] **Standardize Testing:**
    - ~~**Task:** Rename all `_minimal_test.py` to `test_*.py` and move to `tests/unit/`.~~ ✅ Done
    - ~~**Task:** Enforce strict type checking (`mypy --strict`) on `logic_layer`.~~ ✅ Done — extended to full project (369 files, 0 errors).
- [x] **Mirroring System:**
    - **Task:** Flesh out `logic_layer/mirroring.py`. Use references from `source/ground_brush.cpp` (flip logic) to implement map mirroring.

---

## 3. Implementation Guidelines (Sonnet Rules)

1.  **Strict Typing:** No `Any`. Use `TypeAlias` for coordinates (`tuple[int, int, int]`).
2.  **Test First:** Create a `test_brush_house.py` *before* implementing `HouseBrush`.
3.  **Strict Layering:**
    - **Brushes** go in `logic_layer/brushes/`.
    - **Dialogs** go in `vis_layer/ui/main_window/`.
    - **Never** import `PyQt6` in `logic_layer`.
4.  **Legacy Reference:** When in doubt about "how a brush works", read the C++ `source/*_brush.cpp` file. It is the distinct source of truth.

## 4. Next Action
**Recommendation (2026-02-10):** Maintain parity through incremental verification loops:
1. Keep validating UI/UX parity against legacy C++ (`menubar.xml`, popup menus, palette handlers) before each implementation batch.
2. Keep syncing planning artifacts (`Features.md`, `roadmap.json`, `project_tasks.json`, audits) and automation context paths used by Jules.
