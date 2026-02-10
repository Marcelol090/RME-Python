# Documentation Gap Analysis (2026)

**Generated via Deep Audit of codebase `vis_layer` & `logic_layer`**

## 1. Backend Integration Gaps
*   **Code:** `MapCanvasWidget` (`vis_layer/ui/canvas/widget.py`) uses `QPainterRenderBackend` (CPU-based).
*   **Status:** Documented in `system_architecture.xml`.
*   **Future:** `OpenGLBackend` is planned (P0 task) but not active in `MapCanvasWidget`.

## 2. Legacy Features Implementation Status
| Legacy Feature | Python Impl | Documented? | Status |
| :--- | :--- | :--- | :--- |
| **Drawer Protocol** | `vis_layer/renderer/drawers/` | ✅ Yes | Completed & Documented |
| **Brushes (General)** | `logic_layer/` (Flat) | ⚠️ Partial | **Found in logic_layer root**: `door_brush.py`, `zone_brush.py` |
| **Smart Door Brush** | `logic_layer/door_brush.py` | ✅ Yes | Fully Implemented (Mirrors `DoorBrush` CPP) |
| **Flag/Zone Brush** | `logic_layer/zone_brush.py` | ✅ Yes | Fully Implemented (Mirrors `FlagBrush` CPP) |
| **Lasso Selection** | `vis_layer/ui/canvas/widget.py` | ⚠️ Code Only | Logic present (`_lasso_active`, `get_lasso_tool`) |
| **Auto-Border** | `logic_layer/auto_border.py` | ⚠️ Code Only | Implemented |
| **Minimap Mode** | `vis_layer/ui/canvas/widget.py` | ⚠️ Code Only | "Show as minimap" logic in `paintEvent` |
| **Tileset UI** | `vis_layer/ui/panels/tileset_browser.py` | ✅ Yes | Modern PyQt implementation verified (UI-005) |

## 3. Parity Conclusions
*   **Brushes:** Core brushes are implemented in `logic_layer/`.
*   **UI:** Tileset Management is modernized and implemented.
*   **Documentation:** Systems are now better documented.
