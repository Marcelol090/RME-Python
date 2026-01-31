---
applyTo: '**'
priority: high
type: product-requirements
lastUpdated: 2026-01-31
---

# Product Requirements Document (PRD)
## py_rme_canary - Remere's Map Editor Python Implementation

> [!IMPORTANT]
> **For AI Agents:** This document defines the complete product vision, architecture, and requirements for py_rme_canary. Always reference this when making architectural decisions or proposing new features.

---

## 📋 Document Information

| Field | Value |
|:---|:---|
| **Project Name** | py_rme_canary |
| **Document Type** | Product Requirements Document (PRD) |
| **Version** | 2.2.0 |
| **Last Updated** | January 31, 2026 |
| **Status** | Active Development |
| **Author** | Development Team |
| **Classification** | Internal |

---

## 🚀 Executive Summary

**py_rme_canary** is a modern, high-performance Python reimplementation of Remere's Map Editor (RME), built to serve the next generation of Tibia developers. It replaces the legacy C++ codebase with a modular, type-safe, and extensible Python architecture while delivering a premium user experience.

### Vision Statement
To deliver the definitive map editing tool for the Open Tibia community—combining the raw power and familiarity of legacy RME with the modern aesthetics, stability, and extensibility of the Python ecosystem.

### Success Metrics
- **Feature Parity:** 100% of core C++ features (Currently **~92%**)
- **Performance:** Map load time < 2.5s (50MB maps), 60 FPS rendering
- **Stability:** Zero critical bugs in production, memory-safe execution
- **Code Quality:** strict `mypy` compliance, >90% test coverage

---

## 📊 Feature Parity Status

### Current Implementation: ~92% Parity

| Category | Total | Implemented | Partial | Missing | % Complete |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Brushes** | 18 | 17 | 1 | 0 | **94%** |
| **Map I/O** | 7 | 7 | 0 | 0 | **100%** |
| **Editor** | 12 | 12 | 0 | 0 | **100%** |
| **Operations** | 8 | 8 | 0 | 0 | **100%** |
| **UI/UX** | 10 | 10 | 0 | 0 | **100%** |
| **Rendering** | 5 | 5 | 0 | 0 | **100%** |
| **Collaboration** | 4 | 0 | 2 | 2 | **25%** |
| **Total** | **64** | **59** | **3** | **2** | **~92%** |

> **Note:** Updated 2026-01-31. Major milestones achieved in Brushess (Waypoints, Tables, Doors) and Export (PNG, OTMM).

---

## 📦 Product Overview

### Core Capabilities
py_rme_canary is a complete suite for professional map creation:
1.  **Professional Editing:** Full support for OTBM v1/v2, painting, and bulk operations.
2.  **Smart Tools:** Intelligent auto-bordering, brush variations, and prefab placement.
3.  **Visual Excellence:** A modern, dark-themed UI built with PyQT6 and OpenGL.
4.  **Extensibility:** Designed for Python-based plugins and scripting (future).

### Key Differentiators

| Feature | Legacy C++ RME | py_rme_canary |
|:---|:---|:---|
| **Architecture** | Monolithic C++ | Modular Python (Core/Logic/Vis) |
| **UI Framework** | wxWidgets (Dated) | PyQt6 (Modern, Dark Theme) |
| **Rendering** | Legacy OpenGL | Modern OpenGL + QPainter Fallback |
| **Safety** | Manual Memory Mgmt | MemoryGuard (OOM Protection) |
| **Export** | Basic | Advanced (PNG, OTMM, Minimap) |

---

## 🖥️ User Interface & Workflows

py_rme_canary provides a professional, highly customizable dock-based environment designed to streamline map creation.

### Workspace Layout
The application window is divided into four primary interaction zones:

1.  **Central Canvas (Viewport):**
    *   **Role:** The main editing area where the map is rendered.
    *   **Interaction:** Middle-click to pan, Scroll to zoom, Left-click to paint, Right-click for context.
    *   **Features:** Grid toggle (`G`), Floor navigation (`+/-`), Ghosting (previous/next floors).

2.  **Palette Dock (Brush Browser):**
    *   **Role:** The primary tool for selecting what to paint.
    *   **Structure:** Categorized tabs (Ground, Walls, Doodads, Creatures, RAW).
    *   **Usage:** Click a category -> Select a brush -> Ready to paint. Including "Favorites" and "Recent" tabs for speed.

3.  **Properties Dock (Inspector):**
    *   **Role:** Displays and edits details of the selected item or active brush.
    *   **Fields:** ActionID, UniqueID, Destination coordinates (teleports), Depot IDs.
    *   **Flow:** Select Item -> Edit Value in Dock -> Changes apply immediately.

4.  **Minimap & History Docks:**
    *   **Minimap:** Real-time overview. Click to jump camera. Right-click to export.
    *   **History:** Visual stack of Undo/Redo actions. Click any step to revert state.

### Core Workflows

#### 🖌️ Painting & Terminology
*   **Smart Painting:** Select a "Ground Brush" and drag. The system automatically calculates borders and edges (Auto-Bordering).
*   **Variations:** Hold `Ctrl` while painting to cycle through random variations of the tile (if available).
*   **RAW Mode:** Bypass auto-bordering to place frequent raw item IDs directly (using the RAW Palette tab).

#### 🖱️ Selection & Operations
1.  **Select:** Use the **Marquee Tool** (`S`) or **Lasso** to select a region.
2.  **Modify:** Use **Context Menu** on selection to:
    *   *Borderize:* Apply borders to the selection edges.
    *   *Randomize:* Re-roll item variations within the area.
    *   *Copy/Cut:* Standard clipboard operations (`Ctrl+C/X`).

#### 🧭 Item Manipulation
*   **Rotation:** Right-click an item on canvas -> `Rotate` (or `Ctrl+R`).
*   **Properties:** Right-click -> `Properties` to set game logic attributes (e.g., Door keys).
*   **Stack Navigation:** Use the "Browse Field" dialog (Context Menu) to drill down into stacks of items on a single tile.

---

## ✨ Features & Requirements

### 1. Map I/O & Data
Robust handling of map files and external data assets.

- ✅ **OTBM Load/Save:** Streaming parser for v1/v2 maps with atomic saving.
- ✅ **OTMM Support:** Native load/save for the new standard format (`load_otmm`, `save_otmm_atomic`).
- ✅ **External Data:** Full support for `houses.xml`, `spawns.xml`, `zones.xml`.
- ✅ **PNG Export:** Export high-resolution map images (`png_exporter.py`).
- ✅ **Minimap Export:** Generate minimap images (`minimap_exporter.py`).

### 2. Intelligent Brush System
A comprehensive set of painting tools powered by `logic_layer/brush_definitions.py`.

- ✅ **Terrain:** Ground brush with sophisticated auto-bordering.
- ✅ **Walls & Doors:** Smart wall placement and "Door Tool" variations (Locked, Magic, Quest, etc.).
- ✅ **Doodads:** Decorative item placement with randomization.
- ✅ **Create/Erase:** Eraser, optional borders (gravel), and blocking tiles.
- ✅ **Creatures:** Monster and NPC placement (`MonsterBrush`, `NpcBrush`).
- ✅ **Spawns:** Spawn area painting tools (`SpawnMonsterBrush`, `SpawnNpcBrush`).
- ✅ **Waypoints:** Navigation waypoint placement (`WaypointBrush`).
- ✅ **Zones & Flags:** PVP zones and protection flags (`FlagBrush`).
- ✅ **Prefabs:** Carpet and Table brushes with auto-orientation (via definitions).
- ✅ **House:** House tile and exit painting (`HouseBrush`, `HouseExitBrush`).

### 3. Editor Session & Tools
The core interactive experience.

- ✅ **Selection:** Rectangle, lasso, and magic wand selection with add/subtract modes.
- ✅ **Clipboard:** Advanced Copy/Cut/Paste with merge strategies.
- ✅ **History:** Robust Undo/Redo stack with visual history panel.
- ✅ **Gestures:** Intuitive mouse gestures for painting and navigation.
- ✅ **Operations:**
    - Search & Replace Items
    - Borderize / Randomize Selection
    - Move Selection Z-Axis
    - Map Statistics

### 4. UI/UX & Rendering
A premium user interface designed for productivity.

- ✅ **Modern Canvas:** Hardware-accelerated OpenGL rendering (60 FPS target).
- ✅ **Theming:** "Dracula"-inspired dark theme with refined typography and icons.
- ✅ **Dock System:** Flexible layout with Palette, Minimap, Properties, and History docks.
- ✅ **Visual Feedback:** Hoover states, selection highlights, and invalid placement indicators.
- ✅ **Context Menus:** Rich context-sensitive actions for map elements.

---

## 🏗️ System Architecture

### High-Level Design
The project follows a strict **Separation of Concerns** architecture to ensure maintainability and testability.

```mermaid
graph TD
    UI[Vis Layer<br/>(PyQt6 UI)] --> Logic[Logic Layer<br/>(Business Rules)]
    Logic --> Core[Core Layer<br/>(Data & I/O)]

    subgraph Core Layer
        Data[GameMap / Tiles]
        IO[OTBM / XML Parsers]
        Assets[Asset Manager]
    end

    subgraph Logic Layer
        Session[Editor Session]
        Ops[Operations / Brushes]
        History[Undo / Redo]
    end

    subgraph Vis Layer
        Canvas[OpenGL Canvas]
        Docks[Tool Panels]
        Renderer[Render Engine]
    end
```

### Directory Structure
```text
py_rme_canary/
├── core/             # Data models, I/O, & Validation (Zero UI Deps)
├── logic_layer/      # Business logic: Brushes, Operations, Session
├── vis_layer/        # UI implementation: Widgets, Renderer, Themes
├── tools/            # Utilities for data extraction/generation
├── tests/            # Comprehensive test suite (Unit, UI, Perf)
└── docs/             # Documentation & Artifacts
```

---

## 📅 Roadmap & Milestones

### Phase 1: Core Foundation (Completed) ✅
- OTBM I/O, Basic Brushes, Editor Session, Undo/Redo.
- Initial UI implementation and Renderer.

### Phase 2: Feature Parity (Completed) ✅
- [x] Advanced Brushes (Waypoints, Spawns, Houses).
- [x] Map Operations (Search, Replace, Stats).
- [x] Export Tools (PNG, OTMM).
- [x] UI Polish (History Dock, Minimap).

### Phase 3: Advanced Features (Q2 2026) 🔄
- [ ] **Live Collaboration:** Real-time multi-user editing (Foundation in `networked_action_queue.py`).
- [ ] **Plugin API:** Formalize the plugin system for user scripts.
- [ ] **Asset Management:** Enhanced sprite/asset browser.

### Phase 4: Release & Polish (Q3 2026) ⏳
- [ ] Performance Optimization (Render caching, memory tuning).
- [ ] Public Beta Release.
- [ ] Documentation Hub (ReadTheDocs).

---

## 🛡️ Quality Assurance

### Testing Strategy
- **Unit Tests:** >90% coverage for `core/` and `logic_layer/`.
- **UI Tests:** `pytest-qt` for visual regression and interaction testing.
- **Benchmarks:** Automated performance tracking for load/save/render.

### Quality Gates
1.  **Strict Typing:** `mypy --strict` compliance required.
2.  **Linting:** `ruff` with comprehensive rules.
3.  **Complexity:** `radon` enforcement (CC < 10).

---

## 🔍 AI Agent Context

**When implementing new features:**
1.  **Check `brush_definitions.py`** before creating new brush classes; many can be defined data-driven.
2.  **Respect Layers:** Never import `vis_layer` into `core` or `logic_layer`.
3.  **Use `MemoryGuard`:** Always verify memory constraints for large operations.

**Verification Commands:**
```bash
# Run full suite
pytest
# Type check
mypy .
# Lint
ruff check .
```
