# Quality Improvements Report

## 🔒 Security Hardening

Addressed 5 security findings identified by Bandit analysis:

1.  **Subprocess Injection Mitigation (`B603`, `B607`)**:
    *   **File**: `py_rme_canary/quality-pipeline/workers/ai_agent.py`
    *   **Fix**: Replaced partial command paths (`"git"`, `"ruff"`, `"mypy"`) with fully resolved paths using `shutil.which()`. This prevents path hijacking and execution of untrusted binaries from the current working directory.

2.  **XML Injection Prevention (`B314`, `B405`)**:
    *   **Files**:
        *   `py_rme_canary/tests/logic_layer/operations/test_export_statistics.py`
        *   `py_rme_canary/tests/unit/core/io/test_lua_creature_import.py`
    *   **Fix**: Replaced usage of the insecure `xml.etree.ElementTree` library with the project's hardened `py_rme_canary.core.io.xml.safe` module (which uses `defusedxml` internally). This protects against Billion Laughs attacks and external entity expansion.

3.  **Hardcoded Password False Positives (`B105`)**:
    *   **File**: `py_rme_canary/tests/unit/core/protocols/test_live_login_payload.py`
    *   **Fix**: Marked lines containing test passwords with `# nosec` to suppress false positive security warnings in test code.

## 🛠️ Maintainability & Refactoring Candidates

The following components were identified as high-complexity hotspots (Radon CC > 20) and are recommended for refactoring to improve testability and readability.

### 1. `PaletteDock.refresh_list` (Complexity: 89)
*   **Location**: `py_rme_canary/vis_layer/ui/docks/palette.py`
*   **Issue**: This function handles filtering, sorting, and item creation for multiple brush types (Terrain, Doodad, Monster, NPC) in a single monolithic loop/block.
*   **Suggestion**: Implement the **Strategy Pattern**.
    *   Create a `BrushLoaderStrategy` interface.
    *   Implement concrete strategies: `TerrainLoader`, `MonsterLoader`, `NpcLoader`.
    *   `refresh_list` should delegate to the appropriate strategy based on the current tab index.

### 2. `MapCanvas.paintEvent` (Complexity: 82)
*   **Location**: `py_rme_canary/vis_layer/ui/canvas/widget.py`
*   **Issue**: The main rendering loop handles too many responsibilities: background clearing, grid drawing, tile rendering, overlay composition, and tool previews.
*   **Suggestion**: Extract rendering phases into separate helper methods or a `RenderPipeline` class.
    *   `_draw_background()`
    *   `_draw_grid()`
    *   `_draw_content()`
    *   `_draw_overlays()`

### 3. `_export_ground_brush` (Complexity: 54)
*   **Location**: `py_rme_canary/tools/export_brushes_json.py`
*   **Issue**: Deeply nested logic for iterating over tiles and checking attributes.
*   **Suggestion**: Extract attribute extraction logic into a helper function `_extract_tile_attributes(tile) -> dict`.

### 4. `_draw_overlays` (Complexity: 43)
*   **Location**: `py_rme_canary/vis_layer/renderer/opengl_canvas.py`
*   **Issue**: Handles drawing logic for various overlay types (selection, cut, paste, cursor) in one large conditional block.
*   **Suggestion**: Use a registry of `OverlayRenderer` classes keyed by overlay type.

### 5. `build_menus_and_toolbars` (Complexity: 43)
*   **Location**: `py_rme_canary/vis_layer/ui/main_window/build_menus.py`
*   **Issue**: Procedural construction of all UI menus.
*   **Suggestion**: Define menu structures declaratively (e.g., using a dictionary or JSON configuration) and have a builder function construct the QAction objects from that definition.
