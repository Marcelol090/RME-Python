# py_rme_canary - v2.0 Walkthrough

**Last Updated:** 2026-01-29
**Status:** Production Ready

---

## Executive Summary

`py_rme_canary` is a complete Python reimplementation of Remere's Map Editor (RME) with modern architecture, comprehensive testing, and feature parity with the C++ version. This document provides an overview of v2.0 capabilities, architecture, and developer workflows.

---

## Architecture Overview

### Layer Boundaries (Strict)
```
┌──────────────────────────────────────┐
│  vis_layer/ (PyQt6 UI)               │
│  - Dialogs, widgets, rendering       │
├──────────────────────────────────────┤
│  logic_layer/ (Business Logic)       │
│  - Brushes, sessions, operations     │
├──────────────────────────────────────┤
│  core/ (Data Models)                 │
│  - GameMap, Tile, I/O, serialization │
└──────────────────────────────────────┘
```

**Rules:**
- **Core**: No PyQt6, no logic_layer imports
- **Logic**: No PyQt6 (except TYPE_CHECKING), imports core
- **Vis**: Imports core + logic_layer, uses PyQt6

---

## Feature Parity Status

### ✅ Brushes (Complete)
All brush types from C++ RME implemented with TDD:

| Brush Type | File | Tests | Notes |
|------------|------|-------|-------|
| Ground | brush_definitions.py | Full | Auto-border, randomization |
| Wall | brush_definitions.py | Full | Advanced border logic |
| Table | brush_definitions.py | Full | XML parsing parity |
| Carpet | brush_definitions.py | Full | Arrays, borders |
| Door | door_brush.py | Full | State switching |
| Doodad | brush_definitions.py | Full | Erase-like, unique protection |
| House | house_brush.py | Full | Tile properties |
| House Exit | house_exit_brush.py | Full | Exit markers |
| Waypoint | waypoint_brush.py | Full | Position markers |
| Monster | monster_brush.py | Full | Spawn placement |
| NPC | npc_brush.py | Full | NPC placement |
| Spawn (Monster/NPC) | spawn_*_brush.py | Full | Radius, spawn zones |
| Flag | flag_brush.py | Full | PvP/Pz/NoLogout flags |
| Zone | zone_town_dialogs.py | Full | Zone management UI |
| Optional Border | optional_border_brush.py | Full | Conditional borders |
| Eraser | eraser_brush.py | Full | Selective removal |

### ✅ Editor Core (Complete)
| Feature | File | Status |
|---------|------|--------|
| EditorSession | session/editor_session.py | ✅ |
| Selection Modes | session/selection.py | ✅ COMPENSATE/CURRENT/LOWER/VISIBLE |
| Clipboard | clipboard.py | ✅ With cross-version support |
| Undo/Redo | history/action_queue.py | ✅ CompositeAction, stacking |
| Mouse Gestures | session/mouse_gesture.py | ✅ |
| Move Selection | operations/selection_operations.py | ✅ |
| Borderize/Randomize | operations/selection_operations.py | ✅ |
| Duplicate Selection | clipboard.py | ✅ |
| ActionQueue | history/action_queue.py | ✅ Timer reset, labels |
| Networked Actions | networked_action_queue.py | ✅ Broadcast support |

### ✅ Advanced Features (2026-01-28/29)
| Feature | Implementation | Tests |
|---------|----------------|-------|
| Cross-Version Clipboard | cross_version/clipboard.py | 8/8 |
| Sprite Hash Matching | cross_version/sprite_hash.py | 10/10 |
| Auto-Correction | cross_version/auto_correction.py | 11/11 |
| Shortcuts Editor | settings/shortcuts.py | 22/22 |
| Grid Settings | settings/grid_settings.py | 19/19 |
| Light Settings | settings/light_settings.py | 23/23 |
| Search in Selection | operations/selection_operations.py | Full |
| Count Monsters | operations/selection_operations.py | Full |
| Remove Duplicates | operations/selection_operations.py | Full |

### ✅ UI Components
| Component | File | Features |
|-----------|------|----------|
| MapCanvasWidget | canvas/map_canvas_widget.py | OpenGL + QPainter |
| Properties Panel | panels/properties_panel.py | Tile/item editing |
| Find Item Dialog | dialogs/find_item.py | Items/creatures/houses |
| Replace Items Dialog | dialogs/replace_items_dialog.py | Bulk replacement |
| Map Statistics Dialog | dialogs/map_statistics_dialog.py | Counts, analysis |
| Statistics Graphs | dialogs/statistics_graphs_dialog.py | Matplotlib charts |
| Tileset Manager | dialogs/tileset_manager_dialog.py | CRUD, item IDs |
| Take Screenshot | main_window/screenshot.py | PNG export |
| Preferences Window | dialogs/preferences_dialog.py | All settings |
| Browse Tile Window | dialogs/browse_tile_dialog.py | Tile contents |
| Container Properties | dialogs/container_properties_dialog.py | Item containers |
| Import Map Dialog | dialogs/import_map_dialog.py | Merge, offset |
| Brush Size Preview | panels/brush_size_panel.py | Visual preview |
| Paste Preview Overlay | overlays/paste_preview.py | Semi-transparent |
| Drag Shadow | overlays/drag_shadow.py | Selection drag |

### ✅ Map I/O & Assets
| System | Files | Format Support |
|--------|-------|----------------|
| OTBM I/O | core/io/otbm/ | ServerID (v1-4), ClientID (v5-6) |
| OTMM I/O | core/io/otmm.py | Minimap format |
| Minimap | minimap_exporter.py | Export/render |
| Assets Loader | core/loaders/ | DAT, SPR, Appearances |
| Legacy DAT/SPR | core/loaders/legacy/ | 7.4-10.x |
| Appearances | core/loaders/modern/ | 11.0+ |
| Animation Clock | sprite_cache.py | Frame timing |

### ✅ Rendering & Performance
| Feature | Implementation | Tech |
|---------|----------------|------|
| OpenGL Renderer | renderer/opengl_canvas.py | Modern pipeline |
| In-Game Preview | sprite_system/ + preview/ | Isometric, animations |
| Sprite Manager | sprite_cache.py | LRU cache |
| DrawingOptions | drawing_options.py | Flags, previews |
| Lighting | overlays/lighting_overlay.py | Ambient + glow |

### ✅ Live Server/Client
| Feature | File | Capabilities |
|---------|------|--------------|
| State Sync | networked_action_queue.py | Full map sync |
| Action Broadcast | networked_action_queue.py | Undo/redo sync |
| Cursor Broadcast | (integrated) | Multi-user cursors |
| Chat | (integrated) | Text communication |
| Kick/Ban | (integrated) | Host controls |

### ✅ Operations & Tools
| Tool | File | Description |
|------|------|-------------|
| Map Validator | uid_validator.py | UID checks |
| PNG Export/Import | png_exporter.py | Image I/O |
| Export Statistics | operations/export_statistics.py | XML/CSV/JSON |
| Import Creatures | operations/import_creatures.py | XML/Lua folders |
| Replace Items | replace_items.py | Bulk operations |
| Remove Items | remove_items.py | Selective removal |
| Map Format Conversion | map_format_conversion.py | ServerID ↔ ClientID |

---

## Testing Standards

### Coverage Requirements
- **Core/Logic**: ≥90%
- **UI**: ≥60%
- **Integration**: Critical workflows

### Test Patterns
```python
# test_feature.py (22/22 passing example)
def test_feature_basic():
    """Test basic functionality."""
    result = my_function(input_data)
    assert result == expected_value

def test_feature_edge_case():
    """Test edge cases."""
    with pytest.raises(ValueError):
        my_function(invalid_input)
```

### Running Tests
```bash
# All tests
python -m pytest

# Specific module
python -m pytest tests/unit/logic_layer/

# With coverage
python -m pytest --cov=logic_layer tests/unit/logic_layer/
```

---

## Developer Workflow

### Setup
```bash
# Clone
git clone <repo>
cd py_rme_canary

# Install
pip install -e ".[dev]"

# Verify
python -m pytest
python -m mypy logic_layer core
```

### Creating New Features
1. **Plan**: Check IMPLEMENTATION_STATUS.md for parity
2. **Design**: Follow layer boundaries (Opus rules)
3. **Test**: Write tests first (Sonnet TDD)
4. **Implement**: Code with strict type hints
5. **Verify**: Run tests + linters
6. **Document**: Update tracking docs

### Quality Gates
```bash
# Linting
python -m ruff check .
python -m mypy logic_layer core

# Tests
python -m pytest -v

# Coverage
python -m pytest --cov --cov-report=html
```

---

## Documentation Structure

| Document | Purpose |
|----------|---------|
| [IMPLEMENTATION_STATUS.md](../tracking/IMPLEMENTATION_STATUS.md) | Feature parity checklist |
| [MASTER_TODO.md](../tracking/MASTER_TODO.md) | Prioritized backlog |
| [ARCHITECTURE.md](../architecture/PROJECT_STRUCTURE.md) | Layer design |
| [WALKTHROUGH.md](WALKTHROUGH.md) | This document |

---

## Recent Updates (2026-01-28/29)

### Session 1 (2026-01-28)
- Cross-version clipboard with sprite hash matching
- Shortcuts/Grid/Light settings managers
- Selection operations (search, count, dedupe)
- Welcome dialog
- Import creatures from folders

### Session 2 (2026-01-29) - Analysis & Modernization
- C++ RME analysis (534 files, 60+ gaps documented)
- Statistics graphs dialog (Matplotlib)
- Tileset manager dialog
- Drag shadow overlay
- Lighting overlay

### Session 3 (2026-01-29) - Build & Premium UI
- **Compilation**: PyInstaller build script created (`tools/build.py`) with `PySide6` exclusion.
- **Executable**: `dist/CanaryMapEditor.exe` successfully built.
- **Premium UI**: 
  - Dracula Theme implemented (#282a36 background).
  - Glassmorphism effects on tool buttons.
  - Modern animations and transitions in QSS.
  - Rounded corners and refined typography.

---

## Phase 6: Compilation & Modernization (Run)

### Build System
Automated build script using PyInstaller:
```bash
python tools/build.py
```
- Creates single-file executable: `dist/CanaryMapEditor.exe`
- Handles hidden imports (PyQt6, OpenGL, PIL)
- Excludes conflicting bindings (PySide6)

### UI Modernization
- **Theme**: Dracula-inspired Dark Mode
- **Styling**: Advanced QSS with Glassmorphism
- **UX**: Micro-interactions and smooth states

---

## Known Limitations

### Partial Features (⚠️)
- Brush Variation: MVP only, advanced patterns pending
- Brush Thickness: MVP only
- Drag/Smear: Works for selection, partial for brush tools

### Missing Features (❌)
See [MASTER_TODO.md](../tracking/MASTER_TODO.md) for:
- DAT Debug View
- Extension System
- Map Regions
- Advanced Live Mode protocols
- Full rendering pipeline optimizations

---

## Next Steps

1. Investigate RME branches (palette-ux, modern-ui)
2. Implement prioritized missing features
3. Performance optimizations
4. Beta release preparation

---

**For Questions**: See IMPLEMENTATION_STATUS.md or open an issue.
