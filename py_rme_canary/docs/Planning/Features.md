# Remere's Map Editor - Complete Technical Documentation

## Table of Contents

1. [ClientID Format Support (OTBM 5/6)](#clientid-format-support)
2. [Cross-Instance Clipboard System](#cross-instance-clipboard-system)
3. [Advanced Selection Tools](#advanced-selection-tools)
4. [Lua Monster Import](#lua-monster-import)
5. [Quick Replace Features](#quick-replace-features)
6. [Additional Features](#additional-features)
7. [Implementation Tracking](#implementation-tracking)

---

# Implementation Tracking

> **Legend:** `[ ]` = Not implemented | `[/]` = Partial | `[x]` = Complete

## Core Features (RME Extended Edition Parity)

### ClientID/OTBM Support

- [x] ClientID Format Support (OTBM 5/6) → `logic_layer/map_format_conversion.py`
- [x] ServerID Format Support (OTBM 1-4) → `core/io/otbm/`
- [x] Auto ID Translation (ServerID ↔ ClientID) → `core/io/items_otb.py`
- [x] Map Format Conversion → `logic_layer/map_format_conversion.py`
- [x] Appearances.dat Support → `core/assets/appearances_dat.py` (protobuf parser + UI load/unload)

### Clipboard System

- [x] Standard Clipboard (Copy/Paste) → `logic_layer/clipboard.py`
- [x] Cross-Instance Clipboard → `logic_layer/cross_clipboard.py`
- [x] Sprite Hash Matching (FNV-1a) → `logic_layer/sprite_hash.py` + `vis_layer/ui/main_window/qt_map_editor_assets.py`

### Selection Tools

- [x] Rectangular Selection → `vis_layer/ui/canvas/`
- [x] Lasso/Freehand Selection → `logic_layer/lasso_selection.py`
- [x] Floor Selection Modes → `logic_layer/drawing_options.py`

### Import/Export

- [x] Lua Monster Import (Revscript) → `core/io/lua_creature_import.py`
- [x] Minimap PNG Export → `logic_layer/minimap_png_exporter.py`
- [x] Minimap OTMM Export → `logic_layer/minimap_exporter.py`

### Replace Features

- [x] Find & Replace Items → `logic_layer/replace_items.py`
- [x] Remove Items → `logic_layer/remove_items.py`
- [x] Quick Replace from Map → `logic_layer/context_menu_handlers.py`

---

## Brush System

### Core Brushes

- [x] Transactional Brush Base → `logic_layer/transactional_brush.py`
- [x] Raw Brush → `logic_layer/raw_brush.py`
- [x] Eraser Brush → `logic_layer/eraser_brush.py`
- [x] Fill Tool → `logic_layer/fill_tool.py`

### Terrain Brushes

- [x] Brush Definitions → `logic_layer/brush_definitions.py` (81KB)
- [x] Auto Border System → `logic_layer/borders/`
- [x] Door Brush → `logic_layer/door_brush.py`
- [x] Optional Border Brush → `logic_layer/optional_border_brush.py`

### Entity Brushes

- [x] House Brush → `logic_layer/house_brush.py`
- [x] House Exit Brush → `logic_layer/house_exit_brush.py`
- [x] Monster Brush → `logic_layer/monster_brush.py`
- [x] NPC Brush → `logic_layer/npc_brush.py`
- [x] Spawn Monster Brush → `logic_layer/spawn_monster_brush.py`
- [x] Spawn NPC Brush → `logic_layer/spawn_npc_brush.py`

### Zone Brushes

- [x] Zone Brush → `logic_layer/zone_brush.py`
- [x] Waypoint Brush → `logic_layer/waypoint_brush.py`
- [x] Flag Brush → `logic_layer/flag_brush.py`

---

## Advanced Features

### Session Management

- [x] Editor Session → `logic_layer/session/`
- [x] History/Undo System → `logic_layer/history/`
- [x] Autosave Manager → `logic_layer/autosave_manager.py`

### Tools & Utilities

- [x] Ruler Tool → `logic_layer/ruler_tool.py`
- [x] Map Statistics → `logic_layer/map_statistics.py`
- [x] Map Search → `logic_layer/map_search.py`
- [x] Map Diff → `logic_layer/map_diff.py`
- [x] UID Validator → `logic_layer/uid_validator.py`
- [x] Teleport Manager → `logic_layer/teleport_manager.py`

### Rendering & Performance

- [x] Sprite Cache → `logic_layer/sprite_cache.py`
- [x] Render Optimizer → `logic_layer/render_optimizer.py`
- [x] Rust Acceleration → `logic_layer/rust_accel.py` (5 functions: spawn lookup, FNV-1a hash, sprite hash, minimap buffer, PNG IDAT)

### UI/UX C++ Parity (Redux Menu & Dialog Alignment)

- [x] Menu Icons → 55 SVG icons in `vis_layer/ui/resources/icons/` applied to all top-level menus and 40+ QActions
- [x] Settings Dialog (5 tabs) → `vis_layer/ui/dialogs/settings_dialog.py` (General/Editor/Graphics/Interface/Client Version matching C++ 5-tab preferences)
- [x] New Map Dialog → `vis_layer/ui/dialogs/new_map_dialog.py` (client version selector + OTBM format radio buttons)
- [x] Open Map Dialog → `vis_layer/ui/main_window/qt_map_editor_file.py` (OTBM/OTGZ/JSON/OTML/XML filters matching C++)
- [x] Save As Dialog → `vis_layer/ui/main_window/qt_map_editor_file.py` (OTBM + compressed OTGZ filters)
- [x] Placeholder Sprite Rendering → `vis_layer/renderer/opengl_backend.py` + `qpainter_backend.py` (bordered colored squares with item ID text overlay when sprites not loaded)
- [x] "Sprites Not Loaded" Banner → `vis_layer/renderer/opengl_canvas.py` (overlay warning when appearances.dat not loaded)
- [x] Icon Aliases → `vis_layer/ui/resources/icon_pack.py` (16 aliases for menu/action icon reuse)
- [x] Responsive Settings Dialog → QScrollArea wrapping with min/max sidebar widths instead of fixed

#### Part 2 — Deep C++ Menu Parity (build_actions + build_menus)

- [x] Generate Map action → `build_actions.py` + `menubar/file/tools.py` + `qt_map_editor_file.py` (stub dialog)
- [x] Close Map action (Ctrl+Q) → checks unsaved changes, resets to blank 256×256 map
- [x] Export Minimap → `menubar/file/tools.py` + `qt_map_editor_file.py` (PNG/BMP export of current floor)
- [x] Borderize Map → `build_actions.py` + `qt_map_editor_session.py` + `logic_layer/session/editor.py::borderize_map()`
- [x] Randomize Map → `build_actions.py` + `menubar/edit/tools.py`
- [x] Find Everything (map/selection) → `find_item.py::open_find_everything()` (combines unique+action+container+writeable)
- [x] Find Item on Selection → `open_find_dialog(selection_only=True)` filter added
- [x] Edit Towns action (Ctrl+T) → stub dialog in `qt_map_editor_dialogs.py`
- [x] Map Cleanup action → confirmation + removes items with unknown server_ids
- [x] Map Properties (Ctrl+P) → wired to existing `_open_map_properties()`
- [x] Map Statistics (F8) → wired to existing `_show_map_statistics()`
- [x] **View menu** (new) → 14 toggle actions matching C++ (show all floors, minimap, colors, modified, zones, house shader, tooltips, grid, client box, ghost items, ghost floors, shade, client IDs, in-game preview)
- [x] **Show menu** (new) → 14 toggle actions (preview, lights, light strength, technical items, monsters/spawns, NPCs/spawns, special, houses, pathing, towns, waypoints, highlight items, locked doors, wall hooks)
- [x] **Navigate menu** (new) → Go to Previous Position, Go to Position, Jump to Brush, Jump to Item, Floor submenu (0–15), Zoom submenu (In/Out/Normal)
- [x] **Experimental menu** (new) → Fog in light view toggle
- [x] Floor navigation (0–15) → 16 QActions in `act_floor_actions` list, wired to `_goto_floor()` with position history push
- [x] Shortcut conflict resolution → 6 conflicts fixed (Ctrl+D/H, F5, L, U, Esc)
- [x] Forward reference bug fix → `act_goto_previous_position_nav` alias removed (was referencing action before creation)

#### Part 2b — Full C++ Shortcut & Menu Alignment

- [x] **All shortcuts aligned to C++ legacy** → Save As (Ctrl+Alt+S), Replace Items (Ctrl+Shift+F), Remove Items by ID (Ctrl+Shift+R), Show Animation (L), Show Light (Shift+L), Show Houses (Ctrl+H), Highlight Locked Doors (U), About (F1)
- [x] **Editor menu** (new, C++ parity) → New View, Fullscreen, Take Screenshot, Zoom submenu (matched C++ "Editor" as separate menu from "Edit")
- [x] **Edit menu restructured** → Undo/Redo, Replace Items, Border Options submenu, Other Options submenu (new, C++ parity), Cut/Copy/Paste, Global Search, Command Palette
- [x] **Other Options submenu** (C++ Edit menu) → Remove Items by ID, Remove all Corpses, Remove all Unreachable Tiles, Clear Invalid Houses, Clear Modified State
- [x] **Selection menu restructured** → Replace Items on Selection, Find Item on Selection, Remove Item on Selection, Find on Selection submenu, Selection Mode submenu, Borderize/Randomize Selection
- [x] **Window menu restructured** → Minimap, In-Game Preview, New Palette, Palette submenu (T/D/I/H/C/W/R), Toolbars submenu, Actions History, Live Log
- [x] `act_about` (F1) → About dialog with PyRME info, map stats → `qt_map_editor_dialogs.py::_show_about()`
- [x] `act_show_lights` (Shift+L) → Checkable toggle for light rendering → `build_actions.py`
- [x] `act_replace_items_on_selection` → Opens ReplaceItemsDialog pre-filtered to selection → `qt_map_editor_session.py`
- [x] `act_remove_item_on_selection` → Opens FindItemDialog, removes matched items from selection → `qt_map_editor_session.py`
- [x] Label renames to match C++ exactly → "Ghost loose items", "Remove Items by ID...", "Remove all Corpses...", "Remove all Unreachable Tiles...", "Clear Invalid Houses", "Show Animation"
- [x] **Item rendering pipeline fix** → `show_as_minimap` default changed from `True` to `False` so items render as sprites instead of colored rectangles
- [x] Auto-disable minimap mode on sprite load → `_refresh_after_asset_data_load()` clears minimap flag when sprites become available
- [x] **15 new SVG icons** → action_show_lights, action_generate, action_close, action_town, action_cleanup, action_properties, action_statistics, action_borderize, action_show_pathing, action_show_houses, action_animation, action_ingame_preview, action_goto_back, action_randomize, action_remove_item (total: 70 SVG icons)
- [x] Icons added to 18 key menu actions → About, Show Lights, Borderize, Edit Towns, Cleanup, Properties, Statistics, Show Houses, Show Pathing, Show Animation, In-Game Preview, Go To Previous Position, Randomize, Remove Items, Replace/Remove Items on Selection, Generate Map, Close Map

### Scripting

- [x] Script Engine → `logic_layer/script_engine.py` (26KB)

---

## Legacy RME Parity Matrix

| Feature                  | Redux (TFS) | Canary (Modern) | py_rme_canary |
| ------------------------ | :---------: | :-------------: | :-----------: |
| OTBM 1-4 Load/Save       |     ✅      |       ✅        |      ✅       |
| OTBM 5-6 (ClientID)      |     ❌      |       ✅        |      ✅       |
| Cross-Instance Clipboard |     ✅      |       ✅        |      ✅       |
| Lasso Selection          |     ✅      |       ✅        |      ✅       |
| Lua Monster Import       |     ✅      |       ✅        |      ✅       |
| Live Collaboration       |     ✅      |       ✅        |      ✅       |
| All Brush Types          |     ✅      |       ✅        |      ✅       |
| PyQt6 Modern UI          |     ❌      |       ❌        |      ✅       |
| Python Scripting         |     ❌      |       ❌        |      ✅       |
| Menu Icons (70 SVGs)     |     ✅      |       ✅        |      ✅       |
| 5-Tab Preferences        |     ✅      |       ✅        |      ✅       |
| OTGZ Compressed Maps     |     ✅      |       ✅        |      ✅       |
| View/Show/Navigate Menus |     ✅      |       ✅        |      ✅       |
| Floor Navigation (0-15)  |     ✅      |       ✅        |      ✅       |
| Borderize/Randomize Map  |     ✅      |       ✅        |      ✅       |
| Find Everything          |     ✅      |       ✅        |      ✅       |
| C++ Legacy Shortcuts     |     ✅      |       ✅        |      ✅       |
| Item Rendering on Canvas |     ✅      |       ✅        |      ✅       |
| Editor/Edit/Selection    |     ✅      |       ✅        |      ✅       |
| About Dialog (F1)        |     ✅      |       ✅        |      ✅       |

**Legend:** ✅ = Supported | ❌ = Not Supported | ⏳ = Planned

---

# ClientID Format Support (OTBM 5/6)

## 🎯 Overview

RME supports both traditional ServerID-based maps (OTBM 1-4) and modern ClientID-based maps (OTBM 5-6), enabling seamless editing and conversion between formats used by different Open Tibia server distributions.

### What This Means

Open and edit maps created with ClientID-based map editors. This format uses ClientIDs directly instead of ServerIDs, commonly used by modern OT servers like Canary.

**Quick Start:**

1. Load any client version (e.g., Client 14) with its items.otb
2. Open maps in OTBM 5/6 format → Auto-detected
3. IDs translated automatically via items.otb mappings
4. Edit normally → Save in original or converted format

---

## 📖 Background: Understanding the Two ID Systems

### Traditional ServerID System (OTBM 1-4)

**How it works:**

1. Server defines items in `items.otb` with unique ServerIDs
2. Each ServerID has a corresponding ClientID for sprite rendering
3. Maps store ServerIDs
4. Server translates ServerID → ClientID when sending to client
5. Client uses ClientID to display the correct sprite

**Example:**

```
items.otb defines:
  ServerID: 2160 (Crystal Coin)
  ClientID: 3043 (sprite reference)

Workflow:
  Map file: stores "2160"
  Server reads: "2160"
  Server sends to client: "3043"
  Client displays: sprite 3043
```

**Used by:** TFS (The Forgotten Server), OTServ, classic OT distributions

---

### Modern ClientID System (OTBM 5-6)

**How it works:**

1. ClientID and ServerID are unified (ClientID = ServerID)
2. Maps store ClientIDs directly
3. No translation needed - ID goes straight from map to client
4. Item definitions reference `Tibia.dat` or `appearances.dat`

**Example:**

```
Map stores ClientID directly:
  Map file: stores "3043"
  Server reads: "3043"
  Server sends to client: "3043"
  Client displays: sprite 3043
```

**Used by:** Modern OT servers, Canary Server, OTBM 5/6 format maps

---

## 🏗️ System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         RME System Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │  items.otb   │────────▶│ ItemDatabase │                     │
│  │  (required)  │         │   (g_items)  │                     │
│  │              │         │              │                     │
│  │ Contains:    │         │ Stores both: │                     │
│  │ - ServerIDs  │         │ - ServerIDs  │                     │
│  │ - ClientIDs  │         │ - ClientIDs  │                     │
│  │ - Metadata   │         │ - Properties │                     │
│  └──────────────┘         └──────┬───────┘                     │
│                                   │                              │
│                                   ▼                              │
│                          ┌──────────────┐                       │
│                          │ ItemIdMapper │                       │
│                          │              │                       │
│                          │ Builds maps: │                       │
│                          │ S→C and C→S  │                       │
│                          └──────┬───────┘                       │
│                                 │                                │
│  ┌──────────────┐              │              ┌──────────────┐ │
│  │appearances.dat│──────┐       │       ┌─────│   Map File   │ │
│  │  (optional)  │      │       │       │     │  (OTBM 1-6)  │ │
│  │              │      ▼       ▼       ▼     └──────────────┘ │
│  │For extra:    │  ┌─────────────────────┐         ▲          │
│  │- Sprite info │  │     IOMapOTBM       │         │          │
│  │- Metadata    │  │                     │         │          │
│  └──────────────┘  │ - Detects version   │         │          │
│                    │ - Translates IDs    │         │          │
│                    │ - Load/Save logic   │         │          │
│                    └──────────┬──────────┘         │          │
│                               │                     │          │
│                               ▼                     │          │
│                    ┌──────────────────┐            │          │
│                    │  Editor (internal)│───────────┘          │
│                    │                   │                       │
│                    │ Always uses       │                       │
│                    │ ServerIDs         │                       │
│                    └───────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Classes

| Class               | File                       | Purpose                                                          |
| ------------------- | -------------------------- | ---------------------------------------------------------------- |
| ItemIdMapper        | id_mapper.cpp/h            | Builds and stores ServerID ↔ ClientID mappings from items.otb    |
| MapVersion          | client_version.h           | Extended with usesClientIdAsServerId flag and isCanaryFormat()   |
| IOMapOTBM           | iomap_otbm.cpp             | Detects OTBM version, translates IDs on load/save                |
| AppearancesDatabase | appearances_database.cpp/h | Optional protobuf loader for appearances.dat (extra sprite info) |

---

## 🔄 Data Flow: Loading OTBM 5/6 Map (ClientID Format)

### Step-by-Step Process

```
1. User opens map file
   ↓
2. IOMapOTBM::loadMap() is called
   ↓
3. Read OTBM file header
   ├─ Read magic bytes
   ├─ Read OTBM version (finds version 5 or 6)
   └─ Set flag: mapVersion.usesClientIdAsServerId = true
   ↓
4. Begin reading map data (tiles, items, etc)
   ↓
5. For each item found in the map:
   ├─ Read ClientID from file (e.g., 3043)
   ├─ Call ItemIdMapper::clientToServer(3043)
   ├─ Mapper returns ServerID (e.g., 2160)
   └─ Create item internally using ServerID 2160
   ↓
6. Editor now has map loaded
   └─ All items stored with ServerIDs internally
   └─ User can edit normally
```

### Code Flow Example

```cpp
// In IOMapOTBM::loadMap()

// Step 1: Detect format
uint32_t otbm_version = readU32();  // Read version from file

if (otbm_version == MAP_OTBM_5 || otbm_version == MAP_OTBM_6) {
    mapVersion.usesClientIdAsServerId = true;
}

// Step 2: Load items
while (reading_items) {
    uint16_t id_from_file = readU16();  // Read ID from map

    if (mapVersion.usesClientIdAsServerId) {
        // This is a ClientID, translate it
        uint16_t serverId = g_idMapper.clientToServer(id_from_file);

        if (serverId == 0) {
            // Warning: No mapping found for ClientID
            log_warning("ClientID %d has no ServerID mapping", id_from_file);
        }

        // Create item with ServerID
        Item* item = Item::Create(serverId);
    } else {
        // Traditional format - ID is already ServerID
        Item* item = Item::Create(id_from_file);
    }
}
```

---

## 💾 Data Flow: Saving to OTBM 5/6 Map (ClientID Format)

### Step-by-Step Process

```
1. User clicks Save (or Save As)
   ↓
2. IOMapOTBM::saveMap() is called
   ↓
3. Check if saving in ClientID format
   └─ if (mapVersion.isCanaryFormat()) → Yes, OTBM 5/6
   ↓
4. Write OTBM file header
   ├─ Write magic bytes
   ├─ Write version (5 or 6)
   └─ Write map metadata
   ↓
5. Begin writing map data (tiles, items, etc)
   ↓
6. For each item to save:
   ├─ Get ServerID from internal item (e.g., 2160)
   ├─ Call ItemIdMapper::serverToClient(2160)
   ├─ Mapper returns ClientID (e.g., 3043)
   └─ Write ClientID 3043 to file
   ↓
7. File saved successfully
   └─ Map file now contains ClientIDs
```

### Code Flow Example

```cpp
// In IOMapOTBM::saveMap()

// Step 1: Determine format
bool saveAsClientId = mapVersion.isCanaryFormat();

// Step 2: Write header
writeU32(saveAsClientId ? MAP_OTBM_6 : MAP_OTBM_4);

// Step 3: Save items
for (Item* item : items_to_save) {
    uint16_t serverId = item->getID();  // Internal ID is ServerID

    if (saveAsClientId) {
        // Translate ServerID → ClientID
        uint16_t clientId = g_idMapper.serverToClient(serverId);

        if (clientId == 0) {
            // Warning: No mapping found
            log_warning("ServerID %d has no ClientID mapping", serverId);
            clientId = serverId;  // Fallback: use ServerID as-is
        }

        writeU16(clientId);  // Write ClientID to file
    } else {
        // Traditional format
        writeU16(serverId);  // Write ServerID directly
    }
}
```

---

## 🗺️ ItemIdMapper: The Translation Engine

### Purpose

The `ItemIdMapper` class is responsible for building and maintaining the bidirectional mappings between ServerIDs and ClientIDs.

### Building the Mappings

```cpp
class ItemIdMapper {
private:
    // Bidirectional maps
    std::map<uint16_t, uint16_t> m_serverToClient;  // ServerID → ClientID
    std::map<uint16_t, uint16_t> m_clientToServer;  // ClientID → ServerID

public:
    void buildMappingsFromOtb(const ItemDatabase& otbDb) {
        // Iterate through ALL items in items.otb
        for (uint16_t serverId = otbDb.getMinID();
             serverId <= otbDb.getMaxID();
             ++serverId)
        {
            ItemType& itemType = otbDb.getItemType(serverId);

            if (!itemType.isValid()) {
                continue;  // Skip invalid items
            }

            // Get ClientID stored in OTB
            uint16_t clientId = itemType.clientID;

            // Build both directions
            m_serverToClient[serverId] = clientId;
            m_clientToServer[clientId] = serverId;
        }

        // Mappings are now ready for use
    }

    // Translation methods
    uint16_t serverToClient(uint16_t serverId) const {
        auto it = m_serverToClient.find(serverId);
        if (it != m_serverToClient.end()) {
            return it->second;  // Found mapping
        }
        return 0;  // Not found (error)
    }

    uint16_t clientToServer(uint16_t clientId) const {
        auto it = m_clientToServer.find(clientId);
        if (it != m_clientToServer.end()) {
            return it->second;  // Found mapping
        }
        return 0;  // Not found (error)
    }
};
```

### When Mappings Are Built

```
Application Startup
  ↓
Load Client Version (e.g., "14.0")
  ↓
Load items.otb for that version
  ↓
ItemDatabase parses items.otb
  ├─ For each item entry:
  │  ├─ Parse ServerID
  │  ├─ Parse ClientID (already in OTB!)
  │  └─ Store in ItemType
  ↓
ItemIdMapper::buildMappingsFromOtb()
  ├─ Iterate all items
  ├─ Extract ServerID and ClientID
  └─ Build bidirectional maps
  ↓
Mappings ready for use
```

---

## 🔍 Key Technical Points

### 1. Why No Protobuf/appearances.dat Required?

**items.otb already contains ClientIDs:**

- Each OTB entry has BOTH ServerID and ClientID stored
- The OTB format includes a `clientID` field
- When RME loads items.otb, it reads both IDs

**appearances.dat is optional:**

- Only provides extra sprite metadata (animations, colors, etc)
- NOT required for ID translation
- Can be loaded for enhanced sprite information

**Example OTB entry:**

```
Item {
    ServerID: 2160
    ClientID: 3043
    Name: "crystal coin"
    Type: ITEM_TYPE_VALUABLE
    ... other properties
}
```

---

### 2. Editor Always Uses ServerIDs Internally

**Why this design?**

- Consistency: All editing logic works with one ID system
- Compatibility: Existing editor code doesn't need changes
- Translation: Only happens at file I/O boundaries

**Internal representation:**

```cpp
class Item {
private:
    uint16_t id;  // ALWAYS a ServerID

public:
    uint16_t getID() const { return id; }  // Returns ServerID
    // ... other methods
};
```

**Translation only at boundaries:**

- **Loading:** File (ClientID) → Translation → Internal (ServerID)
- **Saving:** Internal (ServerID) → Translation → File (ClientID)
- **Editing:** Always ServerID, no translation needed

---

### 3. OTBM Version Detection

```cpp
enum MapVersionID {
    MAP_OTBM_1 = 0,  // Tibia 7.4  - ServerID format
    MAP_OTBM_2 = 1,  // Tibia 8.0  - ServerID format
    MAP_OTBM_3 = 2,  // Tibia 8.4+ - ServerID format
    MAP_OTBM_4 = 3,  // Tibia 8.7+ - ServerID format
    MAP_OTBM_5 = 4,  // ClientID format (modern)
    MAP_OTBM_6 = 5,  // ClientID format extended
};

struct MapVersion {
    MapVersionID otbm;              // The version number
    bool usesClientIdAsServerId;    // Flag for ClientID maps

    // Helper method
    bool isCanaryFormat() const {
        return usesClientIdAsServerId ||
               otbm >= MAP_OTBM_5;
    }
};
```

**Detection logic:**

```cpp
// When loading a map
uint32_t version = readVersionFromFile();

if (version >= MAP_OTBM_5) {
    mapVersion.usesClientIdAsServerId = true;
    // Use translation when loading/saving
} else {
    mapVersion.usesClientIdAsServerId = false;
    // No translation needed
}
```

---

## 🔄 Map Format Conversion

### Converting ServerID → ClientID (OTBM 1-4 → OTBM 5-6)

```
User selects: Map → Convert Map Format → To ClientID Format
  ↓
For each item in map:
  ├─ Current ID is ServerID (e.g., 2160)
  ├─ Look up in serverToClient map
  ├─ Find ClientID (e.g., 3043)
  └─ Item ID remains 2160 internally (no change needed!)
  ↓
Change mapVersion.usesClientIdAsServerId = true
  ↓
When saving:
  └─ IDs automatically translated to ClientIDs
```

### Converting ClientID → ServerID (OTBM 5-6 → OTBM 1-4)

```
User selects: Map → Convert Map Format → To ServerID Format
  ↓
Items already use ServerIDs internally (no changes needed!)
  ↓
Change mapVersion.usesClientIdAsServerId = false
  ↓
When saving:
  └─ IDs written directly as ServerIDs (no translation)
```

**Key insight:** Because editor always uses ServerIDs internally, conversion is just changing a flag! The actual ID translation happens automatically during save.

---

## 🎨 Features

### Auto ID Translation

- ClientID ↔ ServerID mapping built from items.otb
- Transparent to user during editing
- Preserves item properties and attributes

### No appearances.dat Required

- Works with just items.otb
- Mappings already present in OTB format
- appearances.dat optional for enhanced sprite metadata

### Format Conversion

- Convert maps between ServerID and ClientID formats
- Menu: Map → Convert Map Format...
- Confirm conversion direction
- All item IDs translated automatically

### Show ClientIDs

- Toggle View menu option to display ClientIDs in editor
- Useful when working with ClientID-format maps
- Helps verify correct sprite references

---

## 📁 Appearances Support (Optional)

Optionally load appearances.dat for enhanced ClientID format support and sprite information.

**Actions:**

- Load: File → Appearances → Load Appearances...
- Unload: File → Appearances → Unload Appearances
- Auto-load: Enable in Preferences → Editor tab

**Preferences option:** "Auto-load appearances.dat (ClientID format)" - automatically loads if found in client folder.

---

## 🎮 Client 14 Support

Full support for Client 14 and OTBM versions 5/6. Compatible with maps from various modern OT server projects.

**Supported:**

- OTBM versions: 2, 3, 4, 5, 6
- Data directory: 1100
- Data format: Format 11 (same as Client 11)

---

## ⚠️ Error Handling

### Missing Mappings

**Scenario:** Map contains a ClientID with no ServerID mapping

```cpp
uint16_t serverId = g_idMapper.clientToServer(clientId);

if (serverId == 0) {
    // No mapping found!

    // Log warning
    log_warning("ClientID %d has no ServerID mapping in items.otb",
                clientId);

    // Options:
    // 1. Skip item (lose data)
    // 2. Create placeholder item
    // 3. Use ClientID as ServerID (fallback)

    serverId = clientId;  // Fallback approach
}
```

**User notification:**

- Warning dialog after loading
- List of unmapped IDs
- Recommend updating items.otb

---

## 📊 Example Workflow

### Complete Example: Opening and Saving a ClientID Map

```
1. User: File → Open → selects "canary_map.otbm"

2. RME reads file header
   ↓
   OTBM Version: 6
   ↓
   Set: mapVersion.usesClientIdAsServerId = true

3. RME loads first item:
   ↓
   File contains: ClientID 3043
   ↓
   Call: g_idMapper.clientToServer(3043)
   ↓
   Returns: ServerID 2160
   ↓
   Create: Item(2160) internally

4. User edits map
   ↓
   All operations use ServerID 2160
   ↓
   No translation during editing

5. User: File → Save
   ↓
   Check: mapVersion.isCanaryFormat() → true
   ↓
   For Item(2160):
     Call: g_idMapper.serverToClient(2160)
     Returns: ClientID 3043
     Write: 3043 to file
   ↓
   File saved with ClientIDs
```

---

## 🎯 Summary: ClientID Format

### Key Concepts

1. **Two ID Systems Exist:**
   - Traditional: ServerID in map, translated to ClientID by server
   - Modern: ClientID in map, used directly

2. **RME Bridges Both:**
   - Loads either format seamlessly
   - Translates IDs automatically using items.otb
   - Always uses ServerIDs internally for consistency

3. **items.otb is the Key:**
   - Contains both ServerID and ClientID
   - Source of truth for mappings
   - No protobuf/appearances.dat required for basic functionality

4. **Translation is Transparent:**
   - User doesn't need to think about it
   - Happens automatically during load/save
   - Editing always uses ServerIDs

5. **Format Conversion is Simple:**
   - Just flips a flag
   - IDs translate automatically on save
   - No manual item-by-item conversion needed

---

---

# Cross-Instance Clipboard System

## 🎯 Overview

The Cross-Instance Clipboard system enables copying map content (tiles, items, creatures, spawns) between different RME instances, even when they use incompatible client versions with different item ID schemes. This is achieved through **Sprite Hash Matching** - a technology that creates unique fingerprints of visual sprite data, allowing items to be matched purely by their appearance rather than their IDs.

### Visual Representation

```
SOURCE RME                      TARGET RME
Client 12.x / 13.x              Client 10.x / 11.x
Newer Content                   Receives Content
     ↓                                ↑
   CTRL+C                          CTRL+V
     ↓                                ↑
     └──────────────────┬─────────────┘
                        │
              Clipboard with Sprite Hashes
              FNV-1a 64-bit hash per item
```

---

## 🔍 The Core Problem

### Traditional Clipboard Limitations

**Same-version copying (works fine):**

```
Source RME (Client 12.x)     Target RME (Client 12.x)
Item ID: 2148 (gold coin) → Item ID: 2148 (gold coin)
✓ Same ID, same item, works perfectly
```

**Cross-version copying (breaks):**

```
Source RME (Client 13.x)     Target RME (Client 10.x)
Item ID: 5234 (new item)  → Item ID: 5234 (doesn't exist!)
✗ ID doesn't exist in older client
✗ OR: ID exists but references different item
✗ Result: Wrong item or missing item
```

### Why IDs Don't Work Across Versions

1. **New items added in updates** - Client 13.x has items that didn't exist in 10.x
2. **ID ranges shifted** - Same ID number might reference completely different items
3. **ClientID vs ServerID differences** - Different versions use different ID mapping schemes
4. **Custom server modifications** - Custom items.otb files have unique ID assignments

---

## 💡 The Solution: Sprite Hash Matching

### Core Concept

Instead of relying on item IDs, we create a **visual fingerprint** of each sprite:

```
Traditional Approach (fails):
  Copy item ID 5234 → Paste item ID 5234
  ✗ Different items in different clients

Hash Matching Approach (works):
  Copy item with hash 0x7A3F2B1C8D4E5F6A → Find item with same hash
  ✓ Same pixels = same item, regardless of ID
```

### The Technology Stack

**FNV-1a 64-bit Hashing Algorithm:**

- **Fast** - Minimal performance impact
- **Reliable** - 64-bit provides ~18 quintillion possible values (collision probability ≈ 0)
- **Deterministic** - Same pixels always produce same hash
- **Simple** - Easy to implement and verify

---

## 🚀 Quick Setup Guide

### SOURCE Editor (Copy From)

The RME instance with the newer/different content you want to copy.

**Setting:** Sprite Match on Paste → **OFF**

_This editor only needs to write hashes to the clipboard, not read them._

### TARGET Editor (Paste To)

The RME instance where you want to paste the content.

**Setting:** Sprite Match on Paste → **ON**

_This editor reads the hashes and finds matching items in its own item database._

### Where to Find the Setting

```
Edit Menu → Preferences → Editing → Sprite Match on Paste (cross-version edit)
```

---

## 📋 Prerequisites & Version Compatibility

### Key Concept: It's About YOUR Files

The sprite hash system matches against what's actually in **your** .spr/.dat files, not what the "original" client version contained. This means you can use content from ANY client version as long as you've added the sprites to your own files.

### Requirements for Successful Matching

For an item to be matched successfully, the TARGET editor needs:

1. **Sprite in .spr/.dat** - The visual sprite data must exist in your client files
2. **Item defined in items.otb** - The server ID must be mapped to the correct client ID
3. **Matching pixel data** - The sprite must be visually identical (same pixels = same hash)

### The Matching Flow

```
// What happens when you paste:

1. You add new sprites to your 7.4 .spr/.dat files
2. You define items in items.otb (serverID → clientID mapping)
3. RME builds hash database from YOUR .spr/.dat files at startup
4. On paste: source hash is compared against YOUR local hashes
   → If sprite exists in your files → MATCH
   → If sprite is missing → Red tile (missing sprite)
```

### Compatibility Matrix

| Sprite in YOUR .spr/.dat | items.otb Mapping | Result                                     |
| ------------------------ | ----------------- | ------------------------------------------ |
| ✓ Present                | ✓ Correct         | Works perfectly                            |
| ✓ Present                | ✗ Wrong mapping   | May place different item (hash mismatch)   |
| ✓ Present                | ✗ Not registered  | Red tile (itemID/clientID missing in .otb) |
| ✗ Missing                | —                 | Red tile (sprite not in .spr/.dat)         |

### Version Compatibility Examples

| Scenario                                    | Will It Work? | Notes                                           |
| ------------------------------------------- | ------------- | ----------------------------------------------- |
| 10.98 → 10.77                               | Excellent     | Most items exist in both, high match rate       |
| 12.x → 10.x                                 | Good          | Older items match, newer items need to be added |
| 13.x → 7.4 (vanilla)                        | Limited       | Only items that exist in both will match        |
| 13.x → 7.4 (custom with 13.x sprites added) | Excellent     | If you've added the sprites, they will match!   |

### Pro Tip: Building a Universal Client

You can create a "universal" client by adding sprites from multiple Tibia versions to your .spr/.dat files. This allows you to copy content from ANY version and have it match correctly, regardless of the "base" client version you started with.

**The sprite hash system doesn't care about version numbers - it only cares about pixel data. Same pixels = same hash = successful match.**

---

## 📖 Step-by-Step Instructions

### 1. Open both RME instances

Launch two separate RME editors - one with your source content (newer client) and one with your target map (older/different client).

### 2. Configure the TARGET editor

In the editor where you will PASTE content, enable:

```
Edit → Preferences → Editing → Sprite Match on Paste
```

### 3. Select content in SOURCE editor

Use the selection tool to select the area you want to copy. This includes tiles, items, creatures, and spawns.

### 4. Copy (CTRL+C)

The clipboard now contains all selected content with embedded sprite hashes for each item.

### 5. Paste in TARGET editor (CTRL+V)

The target editor reads the sprite hashes and attempts to find matching items in its database.

---

## 🏗️ System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              Cross-Instance Clipboard Architecture               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SOURCE RME (Client 13.x)        TARGET RME (Client 10.x)       │
│  ┌─────────────────────┐         ┌─────────────────────┐       │
│  │   .spr/.dat files   │         │   .spr/.dat files   │       │
│  │   (newer sprites)   │         │   (older sprites)   │       │
│  └──────────┬──────────┘         └──────────┬──────────┘       │
│             │                                 │                  │
│             ▼                                 ▼                  │
│  ┌─────────────────────┐         ┌─────────────────────┐       │
│  │  SpriteHashBuilder  │         │  SpriteHashBuilder  │       │
│  │                     │         │                     │       │
│  │  Scans all sprites  │         │  Scans all sprites  │       │
│  │  Builds hash→ID map │         │  Builds hash→ID map │       │
│  └──────────┬──────────┘         └──────────┬──────────┘       │
│             │                                 │                  │
│             ▼                                 ▼                  │
│  ┌─────────────────────┐         ┌─────────────────────┐       │
│  │   Hash Database     │         │   Hash Database     │       │
│  │                     │         │                     │       │
│  │ 0xABC...→ ID 5234   │         │ 0xABC...→ ID 2148   │       │
│  │ 0x123...→ ID 3043   │         │ 0x123...→ ID 2160   │       │
│  │ 0x789...→ ID 8472   │         │ (no match)          │       │
│  └──────────┬──────────┘         └──────────┬──────────┘       │
│             │                                 │                  │
│             │    User: CTRL+C                │                  │
│             ▼                                 │                  │
│  ┌─────────────────────┐                     │                  │
│  │  Clipboard Manager  │                     │                  │
│  │                     │                     │                  │
│  │  Serializes:        │                     │                  │
│  │  - Item IDs         │                     │                  │
│  │  - Sprite hashes    │────────────────────▶│                  │
│  │  - Positions        │   System Clipboard  │                  │
│  │  - Attributes       │   (JSON/Binary)     │                  │
│  └─────────────────────┘                     │                  │
│                                               ▼                  │
│                                    ┌─────────────────────┐      │
│                                    │  Clipboard Manager  │      │
│                                    │                     │      │
│                                    │  Deserializes data  │      │
│                                    │  Looks up hashes    │      │
│                                    │  Matches items      │      │
│                                    └──────────┬──────────┘      │
│                                               │                  │
│                          User: CTRL+V         ▼                  │
│                                    ┌─────────────────────┐      │
│                                    │   Item Matcher      │      │
│                                    │                     │      │
│                                    │  Hash 0xABC...      │      │
│                                    │  → Found ID 2148    │      │
│                                    │                     │      │
│                                    │  Hash 0x789...      │      │
│                                    │  → No match (skip)  │      │
│                                    └──────────┬──────────┘      │
│                                               ▼                  │
│                                    ┌─────────────────────┐      │
│                                    │   Map Editor        │      │
│                                    │                     │      │
│                                    │   Places items with │      │
│                                    │   matched local IDs │      │
│                                    └─────────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔨 How Sprite Hash Matching Works

### The Technology

The system uses the **FNV-1a 64-bit hash algorithm** to create a unique digital fingerprint for each sprite. This fingerprint is calculated from the actual pixel data, making it completely independent of item IDs or version numbers.

### Why FNV-1a?

- **Fast** - Minimal performance impact during copy/paste operations
- **Reliable** - 64-bit hash provides extremely low collision probability
- **Deterministic** - Same sprite always produces the same hash

### Hash Calculation Algorithm

```cpp
class SpriteHasher {
public:
    static uint64_t calculateHash(const Sprite& sprite) {
        // FNV-1a 64-bit constants
        const uint64_t FNV_OFFSET_BASIS = 14695981039346656037ULL;
        const uint64_t FNV_PRIME = 1099511628211ULL;

        uint64_t hash = FNV_OFFSET_BASIS;

        // Get raw pixel data
        const uint8_t* pixels = sprite.getPixelData();
        size_t dataSize = sprite.getWidth() * sprite.getHeight() * 4; // RGBA

        // Hash each byte
        for (size_t i = 0; i < dataSize; ++i) {
            hash ^= pixels[i];      // XOR with byte
            hash *= FNV_PRIME;       // Multiply by prime
        }

        return hash;
    }

    // For multi-sprite items (2x2, 3x3, etc)
    static uint64_t calculateCombinedHash(const std::vector<Sprite>& sprites) {
        uint64_t combinedHash = FNV_OFFSET_BASIS;

        for (const Sprite& sprite : sprites) {
            uint64_t spriteHash = calculateHash(sprite);

            // Combine hashes
            combinedHash ^= spriteHash;
            combinedHash *= FNV_PRIME;
        }

        return combinedHash;
    }
};
```

---

### Multi-Layer Matching Process

When you paste, the system uses multiple verification steps to ensure accurate matching:

```
Step 1: Direct ID Check
Does the original item ID exist locally?
  ↓
Step 2: Hash Verification
Does the local sprite hash match the source hash?
  ↓
Step 3: Database Lookup
Search all items for matching sprite hash
```

This multi-layer approach prevents incorrect matches. Even if an item ID exists in both versions, the system verifies that the sprites are actually identical before using it.

### Matching Results

| Result Type | Description                             | What Happens                  |
| ----------- | --------------------------------------- | ----------------------------- |
| EXACT_MATCH | Original ID exists and hash matches     | Item pasted with original ID  |
| HASH_MATCH  | Different ID but same sprite hash found | Item pasted with matched ID   |
| NO_MATCH    | No matching sprite found                | Item skipped or fallback used |
| COLLISION   | Hash exists but might be wrong item     | Best-effort match attempted   |

---

## 🔄 Copy Operation (Source Editor)

### User presses CTRL+C

```cpp
// In ClipboardManager::copySelection()

void ClipboardManager::copySelection(const Selection& selection) {
    ClipboardData clipboardData;

    // Iterate all selected tiles
    for (const Tile* tile : selection.getTiles()) {
        TileData tileData;
        tileData.position = tile->getPosition();

        // Copy items from tile
        for (const Item* item : tile->getItems()) {
            ItemData itemData;

            // Store original ID (for same-version compatibility)
            itemData.originalItemId = item->getID();

            // Calculate sprite hash (for cross-version matching)
            itemData.spriteHash = calculateItemSpriteHash(item);

            // Store all attributes (count, text, etc)
            itemData.attributes = item->getAttributes();

            // Store position within tile
            itemData.stackPosition = item->getStackPosition();

            tileData.items.push_back(itemData);
        }

        // Copy creatures
        if (tile->hasCreature()) {
            CreatureData creatureData;
            creatureData.name = tile->getCreature()->getName();
            creatureData.direction = tile->getCreature()->getDirection();
            tileData.creature = creatureData;
        }

        // Copy spawn data
        if (tile->hasSpawn()) {
            SpawnData spawnData;
            spawnData.size = tile->getSpawn()->getSize();
            spawnData.interval = tile->getSpawn()->getInterval();
            tileData.spawn = spawnData;
        }

        clipboardData.tiles.push_back(tileData);
    }

    // Serialize to system clipboard
    serializeToClipboard(clipboardData);
}
```

### Clipboard Data Structure

```json
{
  "version": 1,
  "sourceClient": "13.40",
  "tiles": [
    {
      "position": { "x": 1000, "y": 1000, "z": 7 },
      "items": [
        {
          "originalId": 5234,
          "spriteHash": "0x7A3F2B1C8D4E5F6A",
          "attributes": {
            "count": 50,
            "actionId": 1001
          },
          "stackPos": 0
        }
      ],
      "creature": {
        "name": "Dragon",
        "direction": "south"
      }
    }
  ]
}
```

---

## 📥 Paste Operation (Target Editor)

### User presses CTRL+V

```cpp
// In ClipboardManager::paste()

void ClipboardManager::paste(const Position& targetPos) {
    // Deserialize clipboard data
    ClipboardData clipboardData = deserializeFromClipboard();

    if (!clipboardData.isValid()) {
        showError("Invalid clipboard data");
        return;
    }

    // Check if sprite matching is enabled
    bool useSpriteMatching = g_settings.getBoolean("spriteMatchOnPaste");

    MatchStatistics stats;

    // Process each tile
    for (const TileData& tileData : clipboardData.tiles) {
        // Calculate paste position (relative to target)
        Position pastePos = calculatePastePosition(
            tileData.position,
            targetPos
        );

        Tile* tile = map.getOrCreateTile(pastePos);

        // Paste items
        for (const ItemData& itemData : tileData.items) {
            Item* pastedItem = nullptr;

            if (useSpriteMatching) {
                // Use sprite hash matching
                MatchResult match = matchItemByHash(itemData);

                if (match.type == MatchType::EXACT_MATCH ||
                    match.type == MatchType::HASH_MATCH)
                {
                    pastedItem = Item::Create(match.matchedItemId);
                    stats.successfulMatches++;
                } else {
                    // No match found
                    stats.failedMatches++;

                    if (g_settings.getBoolean("showMissingItems")) {
                        // Create red placeholder tile
                        pastedItem = Item::Create(ITEM_ID_RED_PLACEHOLDER);
                    } else {
                        continue; // Skip item
                    }
                }
            } else {
                // Traditional mode: use original ID directly
                pastedItem = Item::Create(itemData.originalItemId);
            }

            // Restore attributes
            pastedItem->setAttributes(itemData.attributes);

            // Add to tile
            tile->addItem(pastedItem);
        }

        // Paste creature
        if (tileData.hasCreature()) {
            Creature* creature = Creature::Create(tileData.creature.name);
            if (creature) {
                creature->setDirection(tileData.creature.direction);
                tile->setCreature(creature);
                stats.creaturesPlaced++;
            } else {
                stats.creaturesFailed++;
            }
        }

        // Paste spawn
        if (tileData.hasSpawn()) {
            Spawn* spawn = Spawn::Create(tileData.spawn.size);
            spawn->setInterval(tileData.spawn.interval);
            tile->setSpawn(spawn);
        }
    }

    // Show statistics
    showPasteStatistics(stats);
}
```

---

## 🎯 Multi-Layer Item Matching

### The matching process uses multiple fallback strategies

```cpp
enum class MatchType {
    EXACT_MATCH,     // Same ID exists, hash verified
    HASH_MATCH,      // Different ID, but hash matches
    NO_MATCH,        // No matching sprite found
    COLLISION        // Hash collision (rare)
};

struct MatchResult {
    MatchType type;
    uint16_t matchedItemId;
    float confidence;  // 0.0 - 1.0
};

MatchResult matchItemByHash(const ItemData& itemData) {
    MatchResult result;

    // STEP 1: Try exact ID match with hash verification
    if (g_items.itemExists(itemData.originalItemId)) {
        uint64_t localHash = calculateItemHash(itemData.originalItemId);

        if (localHash == itemData.spriteHash) {
            // Perfect match: same ID, same sprite
            result.type = MatchType::EXACT_MATCH;
            result.matchedItemId = itemData.originalItemId;
            result.confidence = 1.0;
            return result;
        }
        // ID exists but hash doesn't match - fall through to hash lookup
    }

    // STEP 2: Hash database lookup
    auto it = g_hashDatabase.find(itemData.spriteHash);

    if (it != g_hashDatabase.end()) {
        // Found matching sprite with different ID
        result.type = MatchType::HASH_MATCH;
        result.matchedItemId = it->second;
        result.confidence = 0.95;

        // Check for potential collision
        if (g_hashDatabase.count(itemData.spriteHash) > 1) {
            result.type = MatchType::COLLISION;
            result.confidence = 0.70;
            // Use first match, but log warning
            logWarning("Hash collision detected for hash %llu",
                      itemData.spriteHash);
        }

        return result;
    }

    // STEP 3: No match found
    result.type = MatchType::NO_MATCH;
    result.matchedItemId = 0;
    result.confidence = 0.0;

    return result;
}
```

### Why multiple layers?

1. **EXACT_MATCH** - Fast path for same-version copying
2. **HASH_MATCH** - Handles cross-version scenarios
3. **Collision detection** - Safeguards against rare hash conflicts
4. **NO_MATCH** - Graceful handling of missing sprites

---

## 🐉 Creatures and Spawns

The cross-instance clipboard also supports creatures and spawns. These are serialized with their properties and transferred along with the map tiles.

### Creature Data Transferred

- **Name** - The creature type name (e.g., "Demon", "Dragon")
- **Direction** - Which way the creature is facing (N/E/S/W)
- **Spawn Time** - Respawn interval in seconds

### Spawn Data Transferred

- **Size/Radius** - The spawn area radius

**Note:** Creatures are matched by name, not by ID. Both RME instances must have the creature defined in their creature database with the same name for the transfer to work.

---

## 📊 Technical Details

### What Gets Transferred

The clipboard captures and transfers the following data between RME instances:

**Items:**

- Original item ID
- Sprite fingerprint (hash)
- All item attributes
- Position data

**Creatures & Spawns:**

- Creature name
- Facing direction
- Spawn time interval
- Spawn area radius

### Hash Database

When RME starts, it automatically builds a hash database by scanning all sprites in your .spr/.dat files. This creates a lookup table that maps each unique sprite fingerprint to its item ID.

### Performance

**One-time cost:** Hash database is built once at startup

**Fast lookups:** O(1) hash table lookups during paste

**Memory efficient:** Only stores hash-to-ID mappings

**Typical Performance:**

```
Hash Database Building (Startup):
- 10,000 items × ~5 sprites each = 50,000 sprites
- FNV-1a hash: ~50 CPU cycles per sprite
- Total time: < 100ms on modern hardware
- Memory: ~1MB for hash table

Copy Operation:
- Hash calculation: O(n × s) where n=items, s=sprites per item
- Typical: 100 items with 3 sprites each = 300 hashes
- Time: < 5ms

Paste Operation:
- Hash lookup: O(1) per item (hash table)
- Typical: 100 items = 100 lookups
- Time: < 1ms
```

---

## 🔧 Technical Challenges & Solutions

### Challenge 1: Multi-Sprite Items

**Problem:** Some items use multiple sprites (2x2 beds, 3x3 trees, animated water)

**Solution:**

```cpp
// Combine all sprite hashes into one master hash
uint64_t calculateMultiSpriteHash(const ItemType& itemType) {
    std::vector<Sprite> allSprites;

    // Get all sprite variations
    for (int x = 0; x < itemType.width; ++x) {
        for (int y = 0; y < itemType.height; ++y) {
            for (int layer = 0; layer < itemType.layers; ++layer) {
                Sprite sprite = getSpriteAt(itemType, x, y, layer);
                allSprites.push_back(sprite);
            }
        }
    }

    // Combine hashes in deterministic order
    return SpriteHasher::calculateCombinedHash(allSprites);
}
```

---

### Challenge 2: Animated Items

**Problem:** Water, fire, torches have multiple animation frames

**Solution:**

```cpp
// Hash ALL animation frames together
uint64_t calculateAnimatedItemHash(const ItemType& itemType) {
    std::vector<Sprite> allFrames;

    for (int frame = 0; frame < itemType.animationFrames; ++frame) {
        Sprite frameSprite = getAnimationFrame(itemType, frame);
        allFrames.push_back(frameSprite);
    }

    return SpriteHasher::calculateCombinedHash(allFrames);
}
```

**Why this works:** All frames contribute to the hash, so two animated items only match if they have identical animation sequences.

---

### Challenge 3: Item Subtypes

**Problem:** Some items have variations (fluid types, runes with different charges)

**Solution:**

```cpp
// Store separate hashes for each subtype
void buildHashDatabase() {
    for (const ItemType& itemType : g_items) {
        if (itemType.hasSubtypes) {
            // Hash each subtype separately
            for (int subtype = 0; subtype < itemType.maxSubtype; ++subtype) {
                uint64_t hash = calculateHashForSubtype(itemType, subtype);
                g_hashDatabase[hash] = {itemType.id, subtype};
            }
        } else {
            // Single hash for non-subtyped items
            uint64_t hash = calculateItemHash(itemType);
            g_hashDatabase[hash] = {itemType.id, 0};
        }
    }
}
```

---

### Challenge 4: Creatures & Spawns

**Problem:** Creatures don't have sprites in the same way items do

**Solution:**

```cpp
// Creatures matched by NAME, not by sprite hash
struct CreatureData {
    std::string name;  // "Dragon", "Demon", etc
    uint8_t direction;
    // No sprite hash needed
};

// On paste:
Creature* matchCreature(const CreatureData& data) {
    // Look up by name in creature database
    return g_creatures.getCreatureByName(data.name);
}
```

**Why this works:** Creature names are standardized across OT distributions. Both editors need the creature defined with the same name.

---

## 🎯 Real-World Usage Examples

### Example 1: Copying New Decorations from 13.x to 10.x

```
SOURCE (Client 13.40)
User selects area with new decoration items
  └─ Contains: Modern furniture (IDs 35000-35050)
  └─ CTRL+C

Clipboard contains:
  Item ID 35023 → Hash 0xABCDEF1234567890
  Item ID 35024 → Hash 0x1234567890ABCDEF
  ...

TARGET (Client 10.98 + Custom .spr with 13.x sprites added)
User has manually added 13.x sprites to their 10.98 client
  └─ items.otb maps: ServerID 5000 → ClientID 35023
  └─ Hash database built at startup contains:
      Hash 0xABCDEF1234567890 → Local ID 5000

User: CTRL+V
  ├─ Reads hash 0xABCDEF1234567890
  ├─ Looks up in local hash database
  ├─ Finds match: Local ID 5000
  └─ Places item with ID 5000 (correct mapping!)

Result: ✓ New decorations appear correctly!
```

---

### Example 2: Copying Classic Content Between Different Custom Servers

```
SOURCE (Custom Server A - Client 8.6 base)
  └─ Crystal Coin has ID 2357 (custom mapping)
  └─ Sprite hash: 0x9876543210FEDCBA

TARGET (Custom Server B - Client 8.6 base)
  └─ Crystal Coin has ID 2889 (different custom mapping)
  └─ Same sprite, so hash: 0x9876543210FEDCBA

Copy/Paste Flow:
  1. Copy from Server A
     └─ Stores: ID 2357, Hash 0x9876543210FEDCBA

  2. Paste to Server B
     ├─ Try exact match: ID 2357 doesn't exist
     ├─ Try hash lookup: Hash 0x9876543210FEDCBA found
     └─ Match: Local ID 2889

  3. Item placed correctly!
     └─ Even though IDs are different, sprite matched
```

---

## 🎮 User Configuration

### Settings Location

```
Edit → Preferences → Editing → Sprite Match on Paste
```

### Configuration Scenarios

**Scenario 1: Same-Version Copying**

```
Source: Client 12.x
Target: Client 12.x
Setting: OFF (traditional clipboard is faster)
```

**Scenario 2: Cross-Version Copying**

```
Source: Client 13.x (newer content)
Target: Client 10.x (older client)
Setting: ON (enables hash matching)
```

**Scenario 3: One-Way Import**

```
Source: Client 13.x
  └─ Sprite Match: OFF (only writes hashes, doesn't read)

Target: Client 10.x
  └─ Sprite Match: ON (reads hashes, performs matching)
```

---

## 🎨 User Experience Flow

### Visual Feedback During Paste

```
1. User presses CTRL+V
   └─ Progress dialog appears: "Matching sprites..."

2. Matching process runs
   └─ Progress bar updates per item

3. Statistics shown:
   ┌─────────────────────────────────┐
   │  Paste Complete                  │
   ├─────────────────────────────────┤
   │  ✓ 45 items matched successfully │
   │  ⚠ 3 items not found             │
   │  ℹ 2 creatures placed            │
   │  ℹ 1 spawn placed                │
   ├─────────────────────────────────┤
   │  [View Details] [OK]             │
   └─────────────────────────────────┘

4. Red placeholder tiles (if enabled)
   └─ Clearly visible for manual fixing
```

---

## 🐛 Troubleshooting

### Items Not Matching?

- Ensure "Sprite Match on Paste" is enabled on the TARGET editor
- The item might not exist in the target client's .dat/.spr files
- Hash collisions are rare but possible - check if a visually similar item was placed instead

### Creatures Not Appearing?

- The creature must be defined in the target RME's creature database
- Creature names must match exactly (case-sensitive)
- Check that the creatures.xml or monster database is properly loaded

### Performance Issues?

- Large selections with many unique items take longer to hash
- The hash database is built once at startup - subsequent operations are fast
- Consider copying smaller areas if experiencing slowdowns

---

## ⚠️ Limitations & Edge Cases

### Limitation 1: Missing Sprites

**Scenario:**

```
Source has sprite that doesn't exist in target .spr file
  └─ Hash lookup will fail
  └─ Item cannot be matched
```

**Solution:**

```
Options:
1. Skip item (default)
2. Place red placeholder tile
3. Log missing sprite hash for manual addition
```

---

### Limitation 2: Hash Collisions (Extremely Rare)

**Probability:**

```
With 64-bit FNV-1a hash:
- Unique sprites: ~50,000 in typical client
- Hash space: 2^64 = 18,446,744,073,709,551,616
- Collision probability: ~0.0000003%

Practically: Won't happen in normal use
```

**Handling:**

```cpp
if (g_hashDatabase.count(hash) > 1) {
    // Collision detected - use first match but warn
    logWarning("Hash collision: multiple items match hash %llu", hash);
    // Could show user dialog to choose correct item
}
```

---

### Limitation 3: Visually Identical Items

**Problem:**

```
Two different items with identical sprites:
  Item A: "Gold Coin" (usable, stackable)
  Item B: "Fake Gold Coin" (decoration, non-stackable)

Same sprite → Same hash → Will match to first one found
```

**Mitigation:**

```
Priority system:
1. Prefer exact ID match if hash also matches
2. Use item metadata to break ties (flags, type)
3. Allow user to manually correct after paste
```

---

## ✅ Best Practices

1. **Keep both editors open** - The clipboard is shared between instances, so you can paste immediately after copying.

2. **Test with small areas first** - Before copying large sections, test with a small area to verify items are matching correctly.

3. **Check for visual differences** - After pasting, visually inspect the result to ensure items look correct.

4. **Save frequently** - When working with cross-version content, save your work often in case of unexpected issues.

---

## 🔍 Debugging & Troubleshooting

### Debug Mode

**Enable verbose logging:**

```cpp
// In settings
g_settings.setBoolean("debugSpriteMatching", true);

// Logs output:
[SpriteMatch] Copying item ID 5234
[SpriteMatch]   └─ Calculated hash: 0x7A3F2B1C8D4E5F6A
[SpriteMatch]   └─ Sprite dimensions: 32x32, 1 layer
[SpriteMatch] Pasting to target editor
[SpriteMatch]   └─ Looking up hash: 0x7A3F2B1C8D4E5F6A
[SpriteMatch]   └─ Found match: Local ID 2148
[SpriteMatch]   └─ Match type: HASH_MATCH
[SpriteMatch]   └─ Confidence: 95%
```

---

### Export Hash Report

```cpp
// Generate report of all unmatched items
void exportUnmatchedReport(const PasteStatistics& stats) {
    std::ofstream report("unmatched_items.txt");

    report << "Unmatched Items Report\n";
    report << "======================\n\n";

    for (const auto& unmatchedItem : stats.unmatchedItems) {
        report << "Original ID: " << unmatchedItem.originalId << "\n";
        report << "Sprite Hash: 0x" << std::hex << unmatchedItem.hash << "\n";
        report << "Position: " << unmatchedItem.position << "\n";
        report << "\n";
    }

    report << "Total unmatched: " << stats.unmatchedItems.size() << "\n";
}
```

**Users can:**

1. Review which items failed to match
2. Find corresponding sprites in source .spr file
3. Add sprites to target client manually
4. Retry paste operation

---

## 🎯 Summary: Cross-Instance Clipboard

### Key Takeaways

1. **Visual Matching, Not ID Matching**
   - Sprites matched by pixel data, not item IDs
   - Same appearance = same item, regardless of version

2. **FNV-1a Hashing**
   - Fast, reliable, deterministic
   - 64-bit hash space virtually eliminates collisions
   - Same pixels always produce same hash

3. **Multi-Layer Matching**
   - Try exact ID match first (fast path)
   - Fall back to hash lookup (cross-version)
   - Graceful handling of missing sprites

4. **Transparent to User**
   - Enable one setting: "Sprite Match on Paste"
   - Copy/paste works normally
   - Statistics shown after paste

5. **Flexible Client Support**
   - Works with ANY client version combination
   - Only requirement: sprites must exist in target .spr file
   - Custom servers fully supported

### The Magic Formula

```
Same Pixels → Same Hash → Same Item

Regardless of:
- Client version
- Item ID
- ServerID/ClientID differences
- Custom server modifications
```

---

---

# Advanced Selection Tools

## 🎯 Lasso/Freehand Selection

Draw custom polygon shapes to select tiles instead of rectangular selection. Perfect for caves, coastlines, and organic shapes.

### How to Use

1. Click **Lasso button** in Indicators toolbar
2. Make sure you're in **Selection Mode**
3. Hold **Shift + drag** to draw shape
4. Release mouse → polygon closes automatically
5. All tiles inside are selected!

### Keyboard Shortcuts

| Shortcut            | Action            |
| ------------------- | ----------------- |
| Shift + Drag        | Replace selection |
| Ctrl + Shift + Drag | Add to selection  |

### Floor Selection

Respects current floor settings:

- **Current Floor** - Selects only tiles on current floor
- **All Floors** - Selects tiles across all floors
- **Visible Floors** - Selects tiles on visible floors

### Technical Details

Uses **ray casting algorithm** (point-in-polygon) for accurate selection:

```cpp
bool isPointInPolygon(const Point& point, const std::vector<Point>& polygon) {
    int intersections = 0;
    size_t n = polygon.size();

    for (size_t i = 0; i < n; ++i) {
        Point p1 = polygon[i];
        Point p2 = polygon[(i + 1) % n];

        // Ray casting from point to infinity (horizontal ray to the right)
        if ((p1.y > point.y) != (p2.y > point.y)) {
            // Check if ray intersects edge
            double x_intersection = (p2.x - p1.x) * (point.y - p1.y) /
                                   (p2.y - p1.y) + p1.x;

            if (point.x < x_intersection) {
                intersections++;
            }
        }
    }

    // Odd number of intersections = inside polygon
    return (intersections % 2) == 1;
}
```

### Use Cases

**Perfect for:**

- Selecting cave systems with irregular boundaries
- Coastlines and water bodies
- Organic terrain features
- Complex building layouts
- Natural formations (mountains, forests)

**Example workflow:**

```
1. Enable Lasso tool
2. Draw around a cave entrance (freehand)
3. Selection automatically includes all tiles within drawn shape
4. Copy or modify selected area
5. Paste elsewhere maintaining exact shape
```

---

---

# Lua Monster Import

## 🐉 Lua Monster Import (Revscript)

Import monsters from TFS 1.x Lua/revscript format. Supports individual files and recursive folder import.

### Import Methods

**Individual files:**

```
File → Import → Import Monsters/NPC...
```

**Entire folder:**

```
File → Import → Import Monster Folder...
```

### Supported Format

```lua
local mType = Game.createMonsterType("Monster Name")
local monster = {}

monster.outfit = {
    lookType = 130,
    lookHead = 0,
    lookBody = 0,
    lookLegs = 0,
    lookFeet = 0,
    lookAddons = 0,
    lookMount = 0
}

mType:register(monster)
```

### Extracted Data

The importer extracts the following outfit properties:

- **name** - Monster/NPC name
- **lookType** - Outfit type ID
- **lookHead** - Head color (0-132)
- **lookBody** - Body color (0-132)
- **lookLegs** - Legs color (0-132)
- **lookFeet** - Feet color (0-132)
- **lookAddons** - Addons bitmask (0-3)
- **lookMount** - Mount ID (0 = no mount)

### NPC Support

NPCs use `Game.createNpcType()` instead:

```lua
local npcType = Game.createNpcType("NPC Name")
local npc = {}

npc.outfit = {
    lookType = 128,
    lookHead = 57,
    lookBody = 59,
    lookLegs = 40,
    lookFeet = 76,
    lookAddons = 0
}

npcType:register(npc)
```

### Import Behavior

**File Processing:**

- Files without valid definitions are skipped
- Existing monsters are updated (not duplicated)
- Invalid Lua syntax is logged as error

**Folder Import:**

- Recursively scans all subdirectories
- Processes all `.lua` files found
- Shows progress bar for large imports
- Summary dialog shows: imported, skipped, errors

### Technical Implementation

```cpp
struct MonsterOutfit {
    std::string name;
    uint16_t lookType;
    uint8_t lookHead;
    uint8_t lookBody;
    uint8_t lookLegs;
    uint8_t lookFeet;
    uint8_t lookAddons;
    uint16_t lookMount;
};

class LuaMonsterImporter {
public:
    std::vector<MonsterOutfit> importFile(const std::string& filepath) {
        std::vector<MonsterOutfit> outfits;

        // Open and read file
        std::ifstream file(filepath);
        std::string content((std::istreambuf_iterator<char>(file)),
                           std::istreambuf_iterator<char>());

        // Parse with Lua or regex
        parseMonsterScript(content, outfits);

        return outfits;
    }

    void importFolder(const std::string& folderPath) {
        // Recursive directory scan
        for (const auto& entry : fs::recursive_directory_iterator(folderPath)) {
            if (entry.path().extension() == ".lua") {
                auto outfits = importFile(entry.path().string());
                mergeOutfits(outfits);
            }
        }
    }

private:
    void parseMonsterScript(const std::string& content,
                           std::vector<MonsterOutfit>& outfits) {
        // Extract monster name
        std::regex nameRegex(R"(createMonsterType\("([^"]+)"\))");
        std::smatch nameMatch;

        if (!std::regex_search(content, nameMatch, nameRegex)) {
            return; // No valid monster definition
        }

        MonsterOutfit outfit;
        outfit.name = nameMatch[1];

        // Extract outfit values
        extractOutfitValue(content, "lookType", outfit.lookType);
        extractOutfitValue(content, "lookHead", outfit.lookHead);
        extractOutfitValue(content, "lookBody", outfit.lookBody);
        extractOutfitValue(content, "lookLegs", outfit.lookLegs);
        extractOutfitValue(content, "lookFeet", outfit.lookFeet);
        extractOutfitValue(content, "lookAddons", outfit.lookAddons);
        extractOutfitValue(content, "lookMount", outfit.lookMount);

        outfits.push_back(outfit);
    }

    template<typename T>
    void extractOutfitValue(const std::string& content,
                           const std::string& key,
                           T& value) {
        std::regex regex(key + R"(\s*=\s*(\d+))");
        std::smatch match;

        if (std::regex_search(content, match, regex)) {
            value = static_cast<T>(std::stoi(match[1]));
        }
    }
};
```

### Use Cases

**Perfect for:**

- Importing monster definitions from TFS distributions
- Migrating from code-based monster systems to editor
- Batch updating creature outfits
- Synchronizing with server-side monster files

**Workflow example:**

```
1. Export monsters from TFS server (/data/monster/)
2. File → Import → Import Monster Folder...
3. Select folder containing .lua files
4. Review import summary
5. Monsters now available in editor's creature palette
```

---

---

# Quick Replace Features

## ⚡ Quick Replace from Map

Skip the RAW palette! Right-click any item directly on the map to set it as Find or Replace target.

### How to Use

1. Right-click item on map → **"Set as Find Item"**
2. Right-click another item → **"Set as Replace Item"**
3. Press **Ctrl+Shift+F** → Replace Items dialog
4. Click **Replace** → Done!

### Comparison: Before vs After

**Before:**

```
1. Click RAW palette tab
2. Search for item by name/ID
3. Scroll through hundreds of items
4. Right-click item
5. Select "Set as Find Item"
6. Repeat for Replace item
7. Open Replace dialog
```

**Now:**

```
1. Right-click item on map → Set as Find Item
2. Right-click another item → Set as Replace Item
3. Press Ctrl+Shift+F
4. Replace!
```

### Context Menu

When right-clicking an item on the map:

```
┌────────────────────────────┐
│ Copy                       │
│ Cut                        │
│ Paste                      │
├────────────────────────────┤
│ Set as Find Item          │  ← New option
│ Set as Replace Item       │  ← New option
├────────────────────────────┤
│ Properties...              │
│ Remove                     │
└────────────────────────────┘
```

### Replace Dialog Enhancement

**New checkbox:** "Only replace on visible map and current floor"

**Behavior:**

- **Checked**: Limits replacement to visible viewport and current floor only
- **Unchecked**: Replaces throughout entire map (all floors)

**Use cases:**

- Checked: Quick local fixes, testing changes
- Unchecked: Global map-wide replacements

### Technical Implementation

```cpp
class MapCanvas {
private:
    uint16_t findItemId = 0;
    uint16_t replaceItemId = 0;

public:
    void onRightClick(const Position& pos, Item* item) {
        wxMenu contextMenu;

        // Standard options
        contextMenu.Append(ID_COPY, "Copy");
        contextMenu.Append(ID_CUT, "Cut");
        contextMenu.Append(ID_PASTE, "Paste");
        contextMenu.AppendSeparator();

        // Quick replace options
        if (item) {
            contextMenu.Append(ID_SET_FIND_ITEM,
                             wxString::Format("Set as Find Item (ID: %d)",
                                            item->getID()));
            contextMenu.Append(ID_SET_REPLACE_ITEM,
                             wxString::Format("Set as Replace Item (ID: %d)",
                                            item->getID()));
            contextMenu.AppendSeparator();
        }

        // Other options
        contextMenu.Append(ID_PROPERTIES, "Properties...");
        contextMenu.Append(ID_REMOVE, "Remove");

        // Show menu
        PopupMenu(&contextMenu);
    }

    void onSetFindItem(wxCommandEvent& event) {
        if (Item* item = getClickedItem()) {
            findItemId = item->getID();
            statusBar->SetStatusText(
                wxString::Format("Find item set: %d", findItemId)
            );
        }
    }

    void onSetReplaceItem(wxCommandEvent& event) {
        if (Item* item = getClickedItem()) {
            replaceItemId = item->getID();
            statusBar->SetStatusText(
                wxString::Format("Replace item set: %d", replaceItemId)
            );
        }
    }
};
```

### Replace Dialog

```cpp
class ReplaceItemsDialog : public wxDialog {
private:
    wxCheckBox* limitToVisibleCheckbox;

public:
    void onReplace(wxCommandEvent& event) {
        bool limitToVisible = limitToVisibleCheckbox->GetValue();

        if (limitToVisible) {
            // Get visible bounds
            ViewportBounds bounds = mapCanvas->getVisibleBounds();
            int currentFloor = mapCanvas->getCurrentFloor();

            // Replace only in visible area
            replaceInArea(bounds, currentFloor);
        } else {
            // Replace throughout entire map
            replaceInEntireMap();
        }
    }

    void replaceInArea(const ViewportBounds& bounds, int floor) {
        int replaced = 0;

        for (int x = bounds.minX; x <= bounds.maxX; ++x) {
            for (int y = bounds.minY; y <= bounds.maxY; ++y) {
                Tile* tile = map->getTile(x, y, floor);
                if (tile) {
                    replaced += replaceTileItems(tile);
                }
            }
        }

        showResult(replaced);
    }

    void replaceInEntireMap() {
        int replaced = 0;

        // Iterate all tiles in map
        for (Tile* tile : map->getAllTiles()) {
            replaced += replaceTileItems(tile);
        }

        showResult(replaced);
    }

    int replaceTileItems(Tile* tile) {
        int count = 0;

        for (Item* item : tile->getItems()) {
            if (item->getID() == findItemId) {
                // Replace item
                Item* newItem = Item::Create(replaceItemId);
                newItem->copyAttributesFrom(item);

                tile->replaceItem(item, newItem);
                count++;
            }
        }

        return count;
    }
};
```

### Workflow Benefits

**Speed improvement:**

- 7 steps → 3 steps
- No palette navigation needed
- Visual item selection from map
- Immediate context

**Use cases:**

- Quick texture fixes
- Replacing wrong items
- Batch corrections
- Terrain adjustments

---

---

# Additional Features

## 📋 Feature Overview

A collection of quality-of-life improvements and enhancements to the RME editor.

### Monster & NPC Names

**Description:** Creature names are displayed above them on the map for easier identification

**Benefits:**

- Quickly identify creatures without clicking
- Easier spawn management
- Better visual overview of creature distribution

**Technical:**

```cpp
void MapCanvas::renderCreature(Creature* creature, const Position& pos) {
    // Render creature sprite
    renderCreatureSprite(creature, pos);

    // Render name above creature
    if (g_settings.getBoolean("showCreatureNames")) {
        wxString name = creature->getName();
        wxPoint screenPos = worldToScreen(pos);

        // Draw text with background
        dc.SetFont(smallFont);
        wxSize textSize = dc.GetTextExtent(name);

        // Semi-transparent background
        dc.SetBrush(wxBrush(wxColour(0, 0, 0, 128)));
        dc.DrawRectangle(screenPos.x - textSize.x/2,
                        screenPos.y - 24,
                        textSize.x + 4,
                        textSize.y + 2);

        // White text
        dc.SetTextForeground(*wxWHITE);
        dc.DrawText(name, screenPos.x - textSize.x/2, screenPos.y - 24);
    }
}
```

---

### Dark Mode

**Description:** Full dark mode support for the editor UI - easier on the eyes during long mapping sessions

**Features:**

- Dark window backgrounds
- Dark toolbar and menus
- Dark palettes
- Adjusted text colors for readability
- Dark dialog boxes

**Configuration:**

```
Edit → Preferences → Interface → Theme → Dark
```

**Color Scheme:**

```cpp
namespace DarkTheme {
    const wxColour BACKGROUND(30, 30, 30);
    const wxColour FOREGROUND(220, 220, 220);
    const wxColour PANEL(40, 40, 40);
    const wxColour BORDER(60, 60, 60);
    const wxColour HIGHLIGHT(70, 130, 180);
    const wxColour TEXT(240, 240, 240);
}
```

---

### Large Palette Icons

**Description:** Option for larger icons in palettes - better visibility on high-resolution screens

**Configuration:**

```
Edit → Preferences → Interface → Large Palette Icons
```

**Sizes:**

- Normal: 32x32 pixels
- Large: 48x48 pixels
- Extra Large: 64x64 pixels

**Benefits:**

- Better for 4K displays
- Reduced eye strain
- Easier item identification

---

### Palette Right-Click Menu

**Description:** Right-click RAW items to quickly set them as "Find" or "Replace With" targets

**Context Menu:**

```
┌────────────────────────────┐
│ Use Item                   │
│ Properties...              │
├────────────────────────────┤
│ Set as Find Item          │
│ Set as Replace Item       │
├────────────────────────────┤
│ Copy ID                    │
│ Show in Browser           │
└────────────────────────────┘
```

---

### Multiple Instances

**Description:** Run multiple editor instances simultaneously with different SPR/DAT/OTB assets

**Use Cases:**

- Edit different server versions simultaneously
- Compare maps side-by-side
- Copy content between versions
- Test different asset configurations

**Configuration:**

- Each instance loads independent assets
- Separate preferences per instance
- Cross-instance clipboard support

---

### Client Profiles

**Description:** Create multiple data profiles per client version pointing to different asset folders

**Example:**

```
Client 10.98 Profiles:
├─ "10.98-vanilla"     → /data/1098/
├─ "10.98-custom"      → /data/1098-custom/
└─ "10.98-test"        → /data/1098-test/

Each profile contains:
├─ Tibia.spr
├─ Tibia.dat
├─ items.otb
├─ creatures.xml
└─ spawns.xml
```

**Management:**

```
Edit → Client Profiles → Manage Profiles...

┌────────────────────────────────────┐
│ Client Profiles                     │
├────────────────────────────────────┤
│ ☑ 10.98-vanilla        [Edit]      │
│ ☐ 10.98-custom         [Edit]      │
│ ☐ 10.98-test           [Edit]      │
├────────────────────────────────────┤
│ [New Profile] [Delete] [OK]        │
└────────────────────────────────────┘
```

---

### Client 11 Support

**Description:** Added support for loading Client 11 SPR/DAT format

**Technical Details:**

- Extended .dat parser for format 11
- Support for new item flags
- Enhanced sprite format handling
- Backward compatible with older formats

---

### OTMM Export for OTClient

**Description:** Export map as OTMM format - OTClient gets full minimap support immediately

**How to Use:**

```
File → Export → Export Minimap (OTMM)...
```

**Export Options:**

- **Format:** OTMM (binary) or PNG/BMP (image)
- **Floors:** All floors or selected range
- **Colors:** Minimap colors from items.otb
- **Markers:** Include map markers

**OTMM Format:**

```cpp
struct OTMMHeader {
    uint32_t signature;    // 'OTMM'
    uint32_t version;      // Format version
    uint16_t width;        // Map width in tiles
    uint16_t height;       // Map height in tiles
    uint8_t floors;        // Number of floors
};

struct OTMMTile {
    uint8_t color;         // Minimap color
    uint8_t flags;         // Tile flags (walkable, etc)
    uint16_t speed;        // Movement speed
};
```

**Use Case:**

```
1. Create map in RME
2. Export as OTMM
3. Place in OTClient data folder
4. Client automatically shows minimap
5. No server-side minimap generation needed!
```

---

### Duplicate Unique ID Warning

**Description:** Automatic detection and warning when duplicate Unique IDs exist on the map

**When Triggered:**

- Setting a Unique ID that already exists
- Pasting items with duplicate UIDs
- Loading maps with UID conflicts

**Warning Dialog:**

```
┌────────────────────────────────────────┐
│ ⚠ Duplicate Unique ID                  │
├────────────────────────────────────────┤
│ Unique ID 1001 already exists at:      │
│                                         │
│ Position: (1000, 1000, 7)              │
│ Item: Treasure Chest                   │
│                                         │
│ Do you want to use this ID anyway?     │
├────────────────────────────────────────┤
│ [Go to Existing] [Use Anyway] [Cancel] │
└────────────────────────────────────────┘
```

**Technical Implementation:**

```cpp
class UniqueIdManager {
private:
    std::map<uint16_t, Position> uidPositions;

public:
    bool setUniqueId(Item* item, uint16_t uid, const Position& pos) {
        // Check if UID already exists
        auto it = uidPositions.find(uid);

        if (it != uidPositions.end()) {
            // Duplicate found!
            Position existingPos = it->second;

            // Show warning dialog
            int result = showDuplicateWarning(uid, existingPos);

            if (result == ID_GOTO_EXISTING) {
                mapCanvas->centerOnPosition(existingPos);
                return false;
            } else if (result == ID_CANCEL) {
                return false;
            }
            // ID_USE_ANYWAY falls through
        }

        // Set UID
        item->setUniqueId(uid);
        uidPositions[uid] = pos;
        return true;
    }

    void removeUniqueId(uint16_t uid) {
        uidPositions.erase(uid);
    }

    std::vector<uint16_t> findDuplicates() {
        // Scan entire map for duplicate UIDs
        std::map<uint16_t, int> uidCounts;

        for (Tile* tile : map->getAllTiles()) {
            for (Item* item : tile->getItems()) {
                if (item->hasUniqueId()) {
                    uidCounts[item->getUniqueId()]++;
                }
            }
        }

        // Return UIDs that appear more than once
        std::vector<uint16_t> duplicates;
        for (const auto& [uid, count] : uidCounts) {
            if (count > 1) {
                duplicates.push_back(uid);
            }
        }

        return duplicates;
    }
};
```

---

### Position Highlight Box

**Description:** Visual highlight when using Go to Position - precise coordinate placement

**When Active:**

- Using "Go to Position" (Ctrl+G)
- Setting Action IDs at exact positions
- Configuring teleport destinations
- Pasting map areas at specific coordinates

**Visual:**

```
┌─────────────────────┐
│                     │
│   ┏━━━━━━━━━━━┓    │
│   ┃           ┃    │  ← Highlighted tile
│   ┃ (1000,1000,7)  │  ← Position label
│   ┃           ┃    │
│   ┗━━━━━━━━━━━┛    │
│                     │
└─────────────────────┘
```

**Implementation:**

```cpp
class PositionHighlight {
private:
    Position highlightPos;
    wxTimer* fadeTimer;
    float opacity = 1.0f;

public:
    void showHighlight(const Position& pos) {
        highlightPos = pos;
        opacity = 1.0f;

        // Start fade animation
        fadeTimer->Start(50); // 50ms intervals
    }

    void render(wxDC& dc) {
        if (opacity <= 0.0f) return;

        wxPoint screenPos = worldToScreen(highlightPos);

        // Draw pulsing border
        dc.SetPen(wxPen(wxColour(255, 255, 0, opacity * 255), 3));
        dc.SetBrush(*wxTRANSPARENT_BRUSH);
        dc.DrawRectangle(screenPos.x - 2,
                        screenPos.y - 2,
                        TILE_SIZE + 4,
                        TILE_SIZE + 4);

        // Draw position label
        wxString label = wxString::Format("(%d, %d, %d)",
                                         highlightPos.x,
                                         highlightPos.y,
                                         highlightPos.z);

        dc.SetFont(boldFont);
        dc.SetTextForeground(wxColour(255, 255, 0, opacity * 255));
        dc.DrawText(label, screenPos.x, screenPos.y - 20);
    }

    void onFadeTimer() {
        opacity -= 0.05f;

        if (opacity <= 0.0f) {
            fadeTimer->Stop();
        }

        mapCanvas->Refresh();
    }
};
```

**Settings:**

- Duration: 2 seconds (configurable)
- Fade out: Gradual opacity reduction
- Color: Yellow (configurable)
- Border width: 3 pixels

---

## 🎯 Summary

This comprehensive documentation covers:

1. **ClientID Format Support** - Seamless handling of both traditional and modern OTBM formats
2. **Cross-Instance Clipboard** - Copy content between different client versions using sprite hashing
3. **Advanced Selection Tools** - Lasso/freehand selection for complex shapes
4. **Lua Monster Import** - Import creatures from TFS Lua scripts
5. **Quick Replace Features** - Streamlined item replacement workflow
6. **Additional Features** - Quality-of-life improvements for better editing experience

All systems work together to provide a powerful, flexible map editing experience that supports the diverse Open Tibia ecosystem while maintaining ease of use and compatibility across different server distributions and client versions.

---

**Document Version:** 1.1
**Last Updated:** 2026-02-10
**Target Audience:** RME developers, contributors, and advanced users
