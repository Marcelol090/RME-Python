# Product Requirements Document (PRD)

**Project:** py_rme_canary (Modern Remere's Map Editor)
**Version:** 1.0 (Draft)
**Status:** Active
**Author:** Gemini (Principal Architect)

---

## 1. Product Vision
To successfully port and modernize the legacy C++ Remere's Map Editor (RME) into a high-performance, Python-based application using PyQt6. The goal is two-fold:
1.  **Absolute Parity:** Replicate 100% of the functionality of RME git-master (including OTBM support, Live editing, and auto-bordering).
2.  **Premium UX:** Elevate the user experience with reasonable modern design standards (Dark Mode, Glassmorphism, intuitive workflows) while maintaining the familiarity of the classic tool.

## 2. Target Audience
*   **Open Tibia Mappers:** Users creating maps for OT servers (7.4 to 13.x+).
*   **Server Administrators:** Users managing server data and map compatibility.
*   **Content Creators:** Designers requiring precision tools for large-scale world building.

---

## 3. UI/UX Requirements
The interface must scream "Modern & Professional".

### 3.1 Visual Style
*   **Theme:** Native Dark Mode (Dracula or Nord palette) by default. No "standard gray" Qt widgets.
*   **Styling:**
    *   Use `QSS` for comprehensive styling.
    *   Subtle "Glassmorphism" on overlays/panels (semi-transparent backgrounds with blur).
    *   Rounded corners (4px-8px) on containers.
    *   Iconography: High-DPI, vector/SVG icons replacing legacy pixel art icons where appropriate (or upscaled pixel art for nostalgia).

### 3.2 Layout & Interaction
*   **Docking System:** Fully customizable layout using `QDockWidget`. Users can rearrange Palette, Minimap, and Item List.
*   **Responsiveness:** Smooth transitions (e.g., hover states, menu fading).
*   **Feedback:** Immediate visual feedback for actions (e.g., highlighting borders when using the "Magic" brush, clear status bar messages).
*   **Startup Experience:** A "Welcome/Launcher" dialog to select Client Version and Asset Path before loading the main editor.

---

## 4. User Flows

### 4.1 Startup & Configuration
1.  **Launch:** User opens `py_rme_canary`.
2.  **Welcome Dialog:**
    *   User sees "New Map", "Open Map", "Recent Files".
    *   User validates/browses for Tibia Client Data (SPR/DAT).
3.  **Loading:** Progress bar shows asset loading status.
4.  **Main Interface:** The grid rendering the map appears centrally, with tools on the side.

### 4.2 Core Mapping
1.  **Selection:** User selects a "Brush" from the Palette (e.g., "Ground Brush", "Wall Brush").
2.  **Editing:**
    *   **Left-Click:** Places the item/tile. Auto-bordering logic runs instantly.
    *   **Right-Click:** Erases or performs context-specific action.
    *   **Shift + Drag:** Selects a region (Rectangle or Lasso).
3.  **Navigation:**
    *   **Scroll:** Pans the map.
    *   **Ctrl+Scroll:** Zooms in/out.
    *   **PageUp/Down:** Changes floor (Z-axis).

### 4.3 Search & Replace (Productivity)
1.  **Trigger:** User presses `Ctrl+F` (Find) or `Ctrl+H` (Replace).
2.  **Dialog:** A non-blocking dialog appears.
3.  **Action:** User selects "Find Item: Demon" -> List of results appears. Clicking a result jumps the camera to that location.

---

## 5. Functional Requirements
All features must match Legacy RME behavior unless explicitly improved.

### 5.1 Map I/O & Data
*   **Formats:** Load/Save OTBM (versions 1-6), Import XML/OTBM.
*   **Export:** Export Minimap (PNG/OTMM), Export Selection to Image.
*   **Client Support:** Full support for Tibia.dat/Tibia.spr from versions 7.4 through 13.x+.
*   **Profile Management:** Save/Load paths for different client versions (Client Profiles).

### 5.2 Editing Tools (Brushes)
*   **Terrain:** Grass, Water, Cave, etc. (Auto-bordering).
*   **Wall:** Auto-joining walls, different orientations.
*   **Doodad:** Random placement of detail items (rocks, flowers).
*   **Item:** Single generic items (RAW palette).
*   **Creature:** Place Monsters/NPCs (supports Spawn time configuration).
*   **House:** Define house tiles and exit coordinates.
*   **Eraser:** Context-sensitive erasure.
*   **Waypoint:** Add waypoints for NPCs/monsters (legacy feature support).

### 5.3 Advanced Tools
*   **Selection:**
    *   Rectangular Selection.
    *   **[New]** Lasso/Freehand Selection (Polygon).
*   **Transformation:** Copy, Cut, Paste, Rotate Selection.
*   **Automagic:** Borderize Selection, Randomize Selection.
*   **Live Editing:** Host a session, allow other clients to join and edit simultaneously.

### 5.4 Windows & Dialogs
*   **Map Properties:** Edit dimensions, description, author.
*   **Towns:** Manage Town IDs and Temples.
*   **Find/Replace:** Detailed search filters (by item, ID, property).
*   **Minimap:** Real-time navigation aid.
*   **Map Statistics:** Show count of items/creatures.
*   **Extension Manager:** Load/Unload Python/Lua extensions.

### 5.5 Menus
*   **File:** New, Open, Save, Import (Map/Monsters/Minimap), Export (Minimap/Tilesets), Preferences.
*   **Edit:** Undo/Redo, Cut/Copy/Paste, Selection tools.
*   **Map:** Properties, Statistics, Cleanup, Resize, Remove Items/Corpses.
*   **View:** Zoom (In/Out/Normal), Grid, Show shades/ghosting, Fullscreen.
*   **Live:** Host/Join/Settings.
*   **Window:** Manage docked panels (Minimap, Palette, Tool Options).

---

## 6. Technical Constraints
*   **Language:** Python 3.10+
*   **GUI Framework:** PyQt6
*   **Performance:**
    *   Rendering must handle 200x200 visible tiles at 60 FPS.
    *   Large map loads (100MB+ OTBM) must not freeze UI for > 5 seconds (use threading).
*   **Compatibility:** Windows 10/11, Linux (Ubuntu/Debian).

## 7. Dictionary & Terminology
*   **OTBM:** Open Tibia Binary Map format.
*   **Auto-border:** Logic that automatically places edge tiles based on neighbors.
*   **Doodad:** Decorative items placed on top of ground.
*   **CID/SID:** Client ID (sprite ID) vs Server ID (item type ID).
