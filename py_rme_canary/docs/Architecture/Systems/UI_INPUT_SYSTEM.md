# UI Input & Interaction System

**Component:** `vis_layer.ui.canvas.widget.MapCanvasWidget`
**Status:** Implemented (Legacy Parity Active)
**Backend:** `QPainterRenderBackend` (Default)

## Overview
The `MapCanvasWidget` handles all user interactions with the map, including:
*   Mouse Events (Press, Move, Release, Wheel)
*   Keyboard Modifiers (Shift, Ctrl, Alt)
*   Tool Activation (Lasso, Selection, Brushes)
*   Rendering Triggers

## Input Modes & Modifiers

The widget implements RME-compatible input logic (Lines 493-630 of `widget.py`).

| Action | Input Combination | Description |
| :--- | :--- | :--- |
| **Pan Map** | Middle Mouse Button | Drag to pan viewport. |
| **Context Menu** | Right Mouse Button | Opens `ItemContextMenu` for tile under cursor. |
| **Paint (Brush)** | Left Click | Applies current brush (if no selection mode active). |
| **Paint (Alt)** | Alt + Left Click | Applies brush in "Alternate" mode (e.g., Erase for some brushes). |
| **Paste** | Left Click (Armed) | Pastes buffer if `paste_armed` is true. |

### Selection System (`selection_mode = True`)

When `editor.selection_mode` is active, modifiers change behavior:

| Modifiers | Logic Layer Mode | Behavior |
| :--- | :--- | :--- |
| **None** | `REPLACE` | Clears previous checks, starts new Single-Tile selection or Drag. |
| **Shift** | `REPLACE` (Box) | Starts **Box Selection** (clears old). |
| **Ctrl** | `TOGGLE` (Single) | Toggles selection of single tile. |
| **Alt** | `SUBTRACT` (Single) | Removes single tile from selection. |
| **Shift + Ctrl** | `ADD` (Box) | Adds Box to existing selection. |
| **Shift + Alt** | `SUBTRACT` (Box) | Removes Box from existing selection. |
| **Shift + Ctrl + Alt** | `TOGGLE` (Box) | Toggles Box area inclusion. |

## Lasso Tool
**Status:** Implemented (Lines 647-655, 694-706)
**Trigger:** `Shift` + `Lasso Enabled` (UI Toggle)

The Lasso tool allows freehand polygon selection.
1.  **Start:** `Shift + Left Click` (with Lasso enabled).
2.  **Draw:** Mouse Move adds points to `LassoTool`.
3.  **Finish:** Mouse Release closes polygon.
4.  **Apply:** `editor.session.apply_lasso_selection()` calculates tiles inside polygon.

## Rendering Loop
1.  **Request:** `request_render()` triggers `update()`.
2.  **PaintEvent:**
    *   Calculates Visible Bounds.
    *   Calls `_draw_with_map_drawer(painter)`.
    *   **MapDrawer:** Delegates to `FloorDrawer` -> `ItemDrawer` -> `CreatureDrawer`.
    *   **Input Overlays:** Draws Selection Box, Lasso Polygon, and Hover Highlights directly in `paintEvent` (after MapDrawer).
