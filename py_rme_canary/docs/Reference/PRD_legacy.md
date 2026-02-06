# Legacy RME Product Requirements (Reference)
**Source:** Remere's Map Editor (C++ 4.0.0)
**Status:** Legacy Reference
**Purpose:** To document the exact feature set and behavior of the C++ application for parity verification.

---

## 1. System Architecture
*   **Framework:** wxWidgets (GUI) + OpenGL (Rendering).
*   **Threading:** Mostly single-threaded. Specific tasks like loading large maps or live server communication use separate threads but sync heavily with the main thread.
*   **Memory Management:** Manual memory management (new/delete). Map data is loaded entirely into RAM.
*   **Data Structures:**
    *   `Map`: Holds the entire game world, divided into `Tile` objects.
    *   `Tile`: Linked list of `Item` objects.
    *   `Item`: Base class for everything (Ground, Wall, Decor).
    *   `HashedString`: Used for optimized string comparisons.

---

## 2. User Interface (UI)
The interface is a classic MDI (Multiple Document Interface) or Tabbed Interface depending on settings.

### 2.1 Main Window Components
*   **Menubar:** Standard top menu (File, Edit, View, Map, Live, Window, Help).
*   **Toolbar:** Quick access icons (New, Open, Save, Cut/Copy/Paste, Zoom, Floor Up/Down).
*   **Map Canvas:** The central editing area. Renders the map in an isometric view. Supports zooming and scrolling.
    *   **"Gem" Button:** A mode-switching button (often in the status bar or canvas corner) that toggles between "Selection Mode" and "Drawing Mode" (Shortcut: Spacebar).
    *   **Scroll Logic:** Scrolling zooms towards the view center (not cursor). `Ctrl+G` (Go To) compensates for Z-layer offset to center the tile visually.
*   **Sidebars (Dockable):**
    1.  **Palette:** The primary tool for selecting what to draw.
        *   Tabs: Terrain, Doodad, Items, House, Creature, Waypoint, RAW.
    2.  **Minimap:** A pixelated overview of the current floor. Click to navigate.
    3.*   **Tool Options:** Displays settings dynamically based on the active palette tab:
        *   *Terrain/Collection:* Shows Tools (Brush, Circle, Square) and Size.
        *   *Doodad:* Shows Thickness (Variation) and Size.
        *   *Others (Item, Raw, House):* Shows Size only.

### 2.2 Menus
*   **File:** New, Open, Save, Save As, Import (Map, Minimap, Monsters), Export (Minimap, Selection), Preferences, Exit.
*   **Edit:** Undo, Redo, Cut, Copy, Paste, Select All, Find Item, Replace Item, Global Search (`Ctrl+Shift+F`).
*   **Map:** Properties, Statistics, Resize, Cleanup (Remove Items, Remove Corpses, Remove Unreachable, Clean House Items, Clear House Tiles).
*   **View:** Zoom In/Out, Show Grid, Show Creature Information, Show Spawns, Show Houses, Ghosting, Fullscreen, Take Screenshot.
*   **Live:** Host Server, Join Server, Chat, Ban List, Close Server.
*   **Window:** List of open map tabs.
*   **Help:** About, Check for Updates.

### 2.3 Context Menus (Right-Click)
The right-click menu is context-sensitive and highly granular:
*   **Smart Brush Selection:**
    *   **Wall Selected:** Shows "Select Wallbrush".
    *   **Carpet Selected:** Shows "Select Carpetbrush".
    *   **Table Selected:** Shows "Select Tablebrush".
    *   **Creature/Spawn Selected:** Shows "Select Creature/Spawn".
    *   **Door Selected:** Shows "Select Doorbrush".
*   **Item Interactions:**
    *   **Doors:** Toggle Open/Closed.
    *   **Teleports:** "Go To Destination" (jumps camera).
    *   **Rotatable:** "Rotate Item" (cycles through IDs).
*   **Data Actions:**
    *   Copy Item Server/Client ID, Copy Name.
    *   "Browse Field": Opens inspection window for tile stack.

---

## 3. Tools & Brushes
The "Brush" system is the core editing mechanic.

### 3.1 Terrain & Structures (Auto-Bordering)
*   **Ground Brush:** Draws ground tiles. Automatically calculates borders based on neighboring tiles and the brush type (e.g., Grass borders on Dirt).
*   **Wall Brush:** Draws walls. Automatically connects to adjacent walls of the same type.
*   **Door Brush:** Places doors. Can auto-orient based on wall alignment.
*   **Carpet Brush:** Similar to Ground but for overlay items (carpets).
*   **Table Brush:** specialized auto-join logic for tables.

### 3.2 Object Placement
*   **Doodad Brush:** logic for placing randomized details (e.g., rocks, tufts of grass). Can be "One-click" or "Spray".
*   **RAW Palette:** Direct access to every Item ID in `items.otb`. No auto-logic.
*   **Creature Brush:** Places Monsters or NPCs. Stores "Spawn Time".
*   **House Brush:** Marks tiles as belonging to a specific House ID. Also places "Exit" tiles.
*   **Waypoint Brush:** Places waypoints for NPC paths.

### 3.3 Functional Tools
*   **Eraser:** Removes items.
    *   Left-Click: Delete top item / specific type.
    *   Right-Click: Delete ground (if empty).
*   **Selection Tool:**
    *   Rectangular marquee.
    *   Shift+Drag to add.
    *   Actions on Selection: Copy, Cut, Delete, Transform (Rotate).
*   **Magic Wand (Borderize):** Re-calculates borders for the clicked area or selection.

### 3.4 Navigation
*   **Go To Position:** Jump to X, Y, Z.
*   **Go To Town:** Jump to a defined Town Temple.

---

## 4. Dialogs & Modals
*   **Preferences:** General settings, Graphics (OpenGL/DirectX), Network (Live), Client Version paths.
*   **Map Properties:** Map dimensions, description, author.
*   **Towns:** List of towns (ID, Name, Temple Position).
*   **Find Item:** Search database by name/ID.
*   **Replace Items:** Bulk replace Item A with Item B (global or selection).
*   **Import/Export:** various configuration wizards.
*   **Extensions:** Manager for Lua/Python extensions (if supported in that build).

---

## 5. Data Handling
*   **Formats:**
    *   High support for Open Tibia Binary Map (`.otbm`).
    *   Limited/Legacy support for `.otb` (Item definitions) and `.xml` (Monster/NPC imports).
    *   **Items.otb:** The definitions file. RME cannot function without it.
    *   **Tibia.dat / Tibia.spr:** Client assets. RME reads sprites and properties (blocking, solid, etc.) from these.
*   **Extensions:** `materials.xml` defines complex brushes (Grounds, Walls) by linking Item IDs to Brush Logic.

---

## 6. User Workflows
These flows represent the standard usage patterns in the legacy application.

### 6.1 Startup & Initialization
1.  **Launch:** Application starts.
2.  **Welcome Dialog:** Modal dialog appears (can be disabled in Preferences).
    *   Options: "New Map", "Open Map", "Preferences", List of "Recent Maps".
    *   **New Map:** Triggers the New Map wizard (selects client version).
    *   **Open:** Opens system file dialog (OTBM/OTGZ).

### 6.2 Primary Editing Loop
1.  **Tool Selection:** User clicks a tab in **Palette** (e.g., Terrain).
2.  **Brush Selection:** User selects a brush (e.g., Grass).
    *   *System Action:* **Tool Options** panel updates to reflect available settings (Size 1-13, Shape).
3.  **Interaction:**
    *   **Left-Click:** Places tiles. Auto-bordering logic executes immediately to smooth edges.
    *   **Right-Click:** Removes the specific item found by the brush logic (e.g., Grass removes Grass).
    *   **Shift+Left-Click:** Drags a selection box (Rectangle).
    *   **Shift+Right-Click:** Context menu for the top-most item or selection.

### 6.3 Content Management
*   **Importing:** `File -> Import -> Import Map`.
    *   User selects an external OTBM.
    *   RME attempts to merge it into the current coordinate space via a "Paste" operation.
*   **Live Editing:** `Live -> Host (Start)`.
    *   User sets a password and distinct port.
    *   Other users `Live -> Join` with IP/Port.
    *   Changes are synchronized in real-time.
