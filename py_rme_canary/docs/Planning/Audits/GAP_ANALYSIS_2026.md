# Documentation Gap Analysis (2026)

**Generated via Deep Audit of codebase `vis_layer` & `logic_layer`**

## 1. Backend Integration Gaps
*   **Code:** Main editor canvas uses `OpenGLCanvasWidget` (`vis_layer/renderer/opengl_canvas.py`) as central widget.
*   **Status:** OpenGL backend is active with QPainter fallback path and shared map-drawer overlay flow.
*   **Fallback:** `MapCanvasWidget` (`vis_layer/ui/canvas/widget.py`) remains available as QWidget/QPainter compatibility path.

## 2. Legacy Features Implementation Status
| Legacy Feature | Python Impl | Documented? | Status |
| :--- | :--- | :--- | :--- |
| **Drawer Protocol** | `vis_layer/renderer/drawers/` | ✅ Yes | Completed & Documented |
| **Brushes (General)** | `logic_layer/` (Flat) | ⚠️ Partial | **Found in logic_layer root**: `door_brush.py`, `zone_brush.py` |
| **Smart Door Brush** | `logic_layer/door_brush.py` | ✅ Yes | Fully Implemented (Mirrors `DoorBrush` CPP) |
| **Flag/Zone Brush** | `logic_layer/zone_brush.py` | ✅ Yes | Fully Implemented (Mirrors `FlagBrush` CPP) |
| **Lasso Selection** | `vis_layer/ui/canvas/widget.py`, `vis_layer/renderer/opengl_canvas.py` | ✅ Yes | Logic integrated in both canvas paths |
| **Auto-Border** | `logic_layer/auto_border.py` | ⚠️ Code Only | Implemented |
| **Minimap Mode** | `vis_layer/ui/canvas/widget.py`, `vis_layer/renderer/opengl_canvas.py` | ✅ Yes | "Show as minimap" flow and overlays integrated |
| **Tileset UI** | `vis_layer/ui/panels/tileset_browser.py` | ✅ Yes | Modern PyQt implementation verified (UI-005) |

## 3. Parity Conclusions
*   **Brushes:** Core brushes are implemented in `logic_layer/`.
*   **UI:** Tileset Management is modernized and implemented.
*   **Rendering:** OpenGL main pipeline is active with compatibility fallback.
*   **Documentation:** Planning docs require continuous timestamp/status sync to avoid stale audit conclusions.
