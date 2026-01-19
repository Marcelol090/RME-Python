---
applyTo: '**'
priority: high
type: architecture-guide
lastUpdated: 2026-01-14
---

# Project Structure Guide
## py_rme_canary - Ideal Organization & Best Practices

> **For AI Agents:** This document defines the IDEAL project structure, file organization, and naming conventions. ALWAYS follow these patterns when creating new files or refactoring code. Verify against dependency rules before proposing changes.

---

## ��� Document Information

| Field | Value |
|-------|-------|
| **Document Type** | Project Structure Guide |
| **Version** | 1.0.0 |
| **Last Updated** | January 14, 2026 |
| **Purpose** | Define ideal project organization and file structure |
| **Audience** | Developers, Contributors, Maintainers |

---

## ��� Overview

This document defines the **ideal structure** for py_rme_canary, including:
- Directory organization principles
- File naming conventions
- Module boundaries
- Dependency flow
- Best practices for maintainability

---

## ���️ Complete Directory Tree

```
py_rme_canary/
│
├── ��� core/                           # Data Layer (Zero UI Dependencies)
│   ├── __init__.py                   # Core package exports
│   ├── memory_guard.py               # Memory protection system
│   ├── runtime.py                    # Runtime validations & checks
│   │
│   ├── ���️ assets/                    # Asset Management
│   │   ├── __init__.py
│   │   ├── sprite_appearances.py     # Sprite loading & caching
│   │   ├── sprite_cache.py           # LRU sprite cache
│   │   ├── catalog_loader.py         # catalog-content.json loader
│   │   └── fallback_provider.py      # Emergency fallback sprites
│   │
│   ├── ��� config/                    # Configuration Management
│   │   ├── __init__.py
│   │   ├── configuration_manager.py  # Config singleton
│   │   ├── project_definitions.py    # Project schema
│   │   ├── settings.py               # User settings
│   │   └── defaults.py               # Default configurations
│   │
│   ├── ��� constants/                 # Constants & Enums
│   │   ├── __init__.py
│   │   ├── otbm_constants.py         # OTBM format constants
│   │   ├── attribute_constants.py    # Item attributes
│   │   ├── magic_bytes.py            # File format magic bytes
│   │   └── version_constants.py      # Version numbers
│   │
│   ├── ���️ data/                      # Data Models
│   │   ├── __init__.py
│   │   ├── gamemap.py                # GameMap (main container)
│   │   ├── tile.py                   # Tile model
│   │   ├── item.py                   # Item model
│   │   ├── houses.py                 # House data
│   │   ├── spawns.py                 # Spawn areas
│   │   ├── zones.py                  # Zone definitions
│   │   ├── waypoints.py              # Waypoints
│   │   │
│   │   └── models/                   # Sub-models
│   │       ├── __init__.py
│   │       ├── position.py           # Position (x, y, z)
│   │       ├── bounds.py             # Bounding box
│   │       ├── attributes.py         # Attribute containers
│   │       └── load_report.py        # Load report stats
│   │
│   ├── ��� database/                  # Database & Metadata
│   │   ├── __init__.py
│   │   ├── items_xml.py              # items.xml parser
│   │   ├── items_otb.py              # items.otb parser
│   │   ├── id_mapper.py              # Server ID ↔ Client ID mapping
│   │   ├── creatures_xml.py          # creatures.xml parser
│   │   └── cache.py                  # Database cache layer
│   │
│   ├── ��� io/                        # I/O Operations
│   │   ├── __init__.py
│   │   │
│   │   ├── otbm/                     # OTBM Format Handler
│   │   │   ├── __init__.py
│   │   │   ├── loader.py             # Main OTBM loader
│   │   │   ├── saver.py              # Main OTBM saver
│   │   │   ├── streaming.py          # Byte streaming & escape handling
│   │   │   ├── header_parser.py      # Header parsing
│   │   │   ├── tile_parser.py        # Tile parsing
│   │   │   ├── item_parser.py        # Item parsing
│   │   │   ├── node_reader.py        # Generic node reader
│   │   │   ├── validator.py          # OTBM validation
│   │   │   └── version_adapter.py    # Version compatibility layer
│   │   │
│   │   ├── xml/                      # XML Format Handlers
│   │   │   ├── __init__.py
│   │   │   ├── houses_xml.py         # houses.xml parser
│   │   │   ├── spawns_xml.py         # spawns.xml parser
│   │   │   ├── zones_xml.py          # zones.xml parser
│   │   │   └── base_xml_parser.py    # Base XML utilities
│   │   │
│   │   ├── otmm/                     # OTMM Format (Planned)
│   │   │   ├── __init__.py
│   │   │   ├── loader.py
│   │   │   └── saver.py
│   │   │
│   │   └── export/                   # Export Formats (Planned)
│   │       ├── __init__.py
│   │       ├── png_exporter.py       # PNG export
│   │       └── json_exporter.py      # JSON export
│   │
│   ├── ��� protocols/                 # Type Protocols
│   │   ├── __init__.py
│   │   ├── brush_protocol.py         # Brush interface
│   │   ├── loader_protocol.py        # Loader interface
│   │   ├── renderer_protocol.py      # Renderer interface
│   │   └── database_protocol.py      # Database interface
│   │
│   └── ���️ exceptions/                # Custom Exceptions
│       ├── __init__.py
│       ├── io_exceptions.py          # I/O errors
│       ├── validation_exceptions.py  # Validation errors
│       ├── memory_exceptions.py      # Memory errors
│       └── database_exceptions.py    # Database errors
│
├── ��� logic_layer/                    # Business Logic (UI-Agnostic)
│   ├── __init__.py
│   │
│   ├── ���️ brushes/                   # Brush Implementations
│   │   ├── __init__.py
│   │   ├── base_brush.py             # Abstract base brush
│   │   ├── ground_brush.py           # Ground painting
│   │   ├── wall_brush.py             # Wall painting
│   │   ├── doodad_brush.py           # Doodad placement
│   │   ├── table_brush.py            # Table placement
│   │   ├── carpet_brush.py           # Carpet tiling
│   │   ├── door_brush.py             # Door placement
│   │   ├── house_brush.py            # House creation
│   │   ├── spawn_brush.py            # Spawn areas
│   │   ├── waypoint_brush.py         # Waypoints
│   │   ├── eraser_brush.py           # Item erasing
│   │   └── raw_brush.py              # Raw item placement
│   │
│   ├── ��� borders/                   # Auto-Border System
│   │   ├── __init__.py
│   │   ├── processor.py              # Main border processor
│   │   ├── alignment.py              # Border alignment logic
│   │   ├── neighbor_mask.py          # Neighbor detection
│   │   ├── tile_utils.py             # Tile utilities
│   │   ├── border_groups.py          # Border group definitions
│   │   ├── border_friends.py         # Friend/hate relationships
│   │   └── ground_equivalents.py     # Ground equivalence rules
│   │
│   ├── ⏱️ history/                    # Undo/Redo System
│   │   ├── __init__.py
│   │   ├── manager.py                # History manager
│   │   ├── action.py                 # Base action class
│   │   ├── stroke.py                 # Transactional stroke
│   │   ├── paint_action.py           # Paint action
│   │   ├── selection_action.py       # Selection action
│   │   ├── batch_action.py           # Batch action
│   │   └── networked_action.py       # Networked action (planned)
│   │
│   ├── ��� operations/                # Map Operations
│   │   ├── __init__.py
│   │   ├── search.py                 # Search items
│   │   ├── replace.py                # Replace items
│   │   ├── remove.py                 # Remove items
│   │   ├── statistics.py             # Map statistics
│   │   ├── borderize.py              # Borderize selection
│   │   ├── randomize.py              # Randomize selection
│   │   ├── transform.py              # Transform operations
│   │   └── validate.py               # Validation operations
│   │
│   ├── ��� session/                   # Editor Session
│   │   ├── __init__.py
│   │   ├── editor.py                 # EditorSession (main controller)
│   │   ├── selection.py              # Selection manager
│   │   ├── clipboard.py              # Clipboard manager
│   │   ├── gestures.py               # Mouse gesture handler
│   │   ├── move.py                   # Move selection
│   │   ├── viewport.py               # Viewport state
│   │   └── tool_state.py             # Tool state manager
│   │
│   ├── brush_definitions.py          # Brush definitions & registry
│   ├── brush_factory.py              # Brush factory
│   ├── auto_border.py                # Legacy auto-border (deprecated)
│   ├── geometry.py                   # Geometric utilities
│   ├── mirroring.py                  # Mirroring operations
│   ├── transactional_brush.py        # Transactional brush wrapper
│   └── map_validator.py              # Map validation logic
│
├── ���️ vis_layer/                     # Presentation Layer (UI)
│   ├── __init__.py
│   ├── qt_app.py                     # Main application entry point
│   │
│   ├── ��� renderer/                  # Rendering System
│   │   ├── __init__.py
│   │   ├── render_model.py           # Qt-free draw commands
│   │   ├── opengl_canvas.py          # OpenGL renderer
│   │   ├── qpainter_canvas.py        # QPainter fallback
│   │   ├── drawing_options.py        # Drawing options (grid, flags)
│   │   ├── layer_manager.py          # Render layers
│   │   └── sprite_renderer.py        # Sprite rendering utilities
│   │
│   ├── ���️ ui/                        # UI Components
│   │   ├── __init__.py
│   │   ├── theme.py                  # Design token system
│   │   ├── base_style.qss            # Base QSS styles
│   │   ├── dark_theme.qss            # Dark theme overrides
│   │   ├── light_theme.qss           # Light theme overrides
│   │   │
│   │   ├── main_window/              # Main Window
│   │   │   ├── __init__.py
│   │   │   ├── editor.py             # QtMapEditor (main window)
│   │   │   ├── qt_map_editor_file_ops.py      # File operations mixin
│   │   │   ├── qt_map_editor_edit_ops.py      # Edit operations mixin
│   │   │   ├── qt_map_editor_view_ops.py      # View operations mixin
│   │   │   ├── qt_map_editor_tool_ops.py      # Tool operations mixin
│   │   │   │
│   │   │   └── menubar/              # Menu Bar Components
│   │   │       ├── __init__.py
│   │   │       ├── file_menu.py      # File menu
│   │   │       ├── edit_menu.py      # Edit menu
│   │   │       ├── view_menu.py      # View menu
│   │   │       ├── map_menu.py       # Map menu
│   │   │       ├── tools_menu.py     # Tools menu
│   │   │       └── help_menu.py      # Help menu
│   │   │
│   │   ├── canvas/                   # Map Canvas
│   │   │   ├── __init__.py
│   │   │   ├── map_canvas.py         # Main canvas widget
│   │   │   ├── canvas_controller.py  # Canvas controller
│   │   │   ├── viewport.py           # Viewport management
│   │   │   ├── zoom.py               # Zoom handler
│   │   │   ├── pan.py                # Pan handler
│   │   │   └── overlay.py            # Canvas overlays (grid, selection)
│   │   │
│   │   ├── docks/                    # Dock Widgets
│   │   │   ├── __init__.py
│   │   │   ├── palette.py            # Brush palette dock
│   │   │   ├── minimap.py            # Minimap dock
│   │   │   ├── properties.py         # Properties dock (inspector)
│   │   │   ├── history.py            # History dock (undo/redo)
│   │   │   ├── layers.py             # Layers dock
│   │   │   └── search.py             # Search dock
│   │   │
│   │   ├── dialogs/                  # Dialogs
│   │   │   ├── __init__.py
│   │   │   ├── preferences.py        # Preferences dialog
│   │   │   ├── new_map.py            # New map dialog
│   │   │   ├── map_properties.py     # Map properties dialog
│   │   │   ├── search_replace.py     # Search & replace dialog
│   │   │   ├── statistics.py         # Statistics dialog
│   │   │   └── about.py              # About dialog
│   │   │
│   │   ├── widgets/                  # Reusable Widgets
│   │   │   ├── __init__.py
│   │   │   ├── brush_selector.py     # Brush selector widget
│   │   │   ├── item_selector.py      # Item selector widget
│   │   │   ├── color_picker.py       # Color picker
│   │   │   ├── size_selector.py      # Brush size selector
│   │   │   └── status_widget.py      # Status bar widget
│   │   │
│   │   └── helpers/                  # UI Helpers
│   │       ├── __init__.py
│   │       ├── indicators.py         # Indicator service
│   │       ├── keyboard.py           # Keyboard handler
│   │       ├── shortcuts.py          # Shortcut manager
│   │       └── tooltips.py           # Tooltip utilities
│   │
│   └── tk_app.py                     # Legacy Tkinter app (deprecated)
│
├── ���️ tools/                         # Utility Scripts
│   ├── __init__.py
│   ├── export_brushes_json.py        # Export brushes to JSON
│   ├── read_otbm_header.py           # Read OTBM header info
│   ├── validate_doodads_in_memory.py # Validate doodads
│   ├── updater.py                    # Auto-updater
│   │
│   ├── ast_rules/                    # AST-grep Rules
│   │   ├── anti-patterns.yml         # Anti-pattern detection
│   │   └── modernization.yml         # Modernization rules
│   │
│   └── libcst_transforms/            # LibCST Transformers
│       ├── __init__.py
│       └── modernize_typing.py       # Typing modernization
│
├── ��� tests/                         # Test Suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration
│   │
│   ├── unit/                         # Unit Tests
│   │   ├── __init__.py
│   │   ├── core/                     # Core layer tests
│   │   │   ├── test_gamemap.py
│   │   │   ├── test_tile.py
│   │   │   ├── test_item.py
│   │   │   ├── test_otbm_loader.py
│   │   │   └── test_items_xml.py
│   │   │
│   │   ├── logic_layer/              # Logic layer tests
│   │   │   ├── test_editor_session.py
│   │   │   ├── test_selection.py
│   │   │   ├── test_clipboard.py
│   │   │   ├── test_brushes.py
│   │   │   └── test_auto_border.py
│   │   │
│   │   └── tools/                    # Tool tests
│   │       └── test_export_brushes.py
│   │
│   ├── ui/                           # UI Tests (pytest-qt)
│   │   ├── __init__.py
│   │   ├── test_qt_map_editor.py
│   │   ├── test_map_canvas.py
│   │   ├── test_palette.py
│   │   └── test_dialogs.py
│   │
│   ├── integration/                  # Integration Tests
│   │   ├── __init__.py
│   │   ├── test_load_save_roundtrip.py
│   │   ├── test_edit_workflow.py
│   │   └── test_end_to_end.py
│   │
│   ├── performance/                  # Performance Tests
│   │   ├── __init__.py
│   │   ├── bench_load.py             # Load benchmarks
│   │   ├── bench_save.py             # Save benchmarks
│   │   └── bench_render.py           # Render benchmarks
│   │
│   └── fixtures/                     # Test Fixtures
│       ├── __init__.py
│       ├── maps/                     # Test map files
│       ├── items/                    # Test item files
│       └── mocks/                    # Mock objects
│
├── ��� docs/                          # Documentation
│   ├── PRD.md                        # Product Requirements Document (this file)
│   ├── PROJECT_STRUCTURE.md          # Project structure guide
│   ├── ARCHITECTURE.md               # Architecture overview
│   ├── IMPLEMENTATION_STATUS.md      # Feature parity checklist
│   ├── IMPLEMENTATION_TODO.md        # Actionable TODOs
│   ├── WALKTHROUGH.md                # Development walkthrough
│   ├── TODO_EXPENSIVE.md             # Technical debt
│   ├── CONTRIBUTING.md               # Contributing guide
│   ├── CHANGELOG.md                  # Version changelog
│   ├── ROLLOUT_PLAN.md               # Release plan
│   ├── MIGRATION_GUIDE_v2.1.md       # Migration guide
│   ├── QUALITY_CHECKLIST.md          # Quality checklist
│   ├── quality_pipeline_guide.md     # Quality pipeline docs
│   ├── memory_instruction.md         # Memory system docs
│   ├── agents.md                     # AI agent docs
│   ├── LEGACY_GUI_MAPPING.md         # Legacy GUI mapping
│   ├── ANALISE_FALTANTE.md           # Missing features analysis
│   ├── ANALISE_PY_RME_CANARY_2025.md # 2025 audit
│   └── GUI_TESTING_GUIDE.md          # GUI testing guide
│
├── ��� quality-pipeline/              # Quality Pipeline (v2.1)
│   ├── quality.sh                    # Main pipeline orchestrator
│   ├── pyproject.toml                # Pipeline dependencies
│   ├── verify_p4.bat                 # Phase 4 verification
│   │
│   ├── config/                       # Pipeline Configuration
│   │   ├── quality.yaml              # Main config
│   │   ├── ruff.toml                 # Ruff config
│   │   └── mypy.ini                  # Mypy config
│   │
│   ├── modules/                      # Pipeline Modules
│   │   ├── copilot_integration.sh    # Copilot integration
│   │   ├── antigravity_integration.sh # Antigravity integration
│   │   └── llm_rule_generator.sh     # LLM rule generator
│   │
│   ├── workers/                      # Python Workers
│   │   ├── __init__.py
│   │   ├── copilot_client.py         # Copilot API client
│   │   ├── antigravity_client.py     # Antigravity API client
│   │   ├── rule_generator.py         # Rule generator
│   │   ├── ai_agent.py               # AI agent
│   │   ├── pool_manager.py           # Worker pool manager
│   │   └── phase4_verifier.py        # Phase 4 verifier
│   │
│   └── .quality_reports/             # Quality Reports
│       ├── phase4_verification.json  # Phase 4 results
│       └── ruff_baseline.json        # Ruff baseline
│
├── ��� reports/                       # Analysis Reports
│   ├── issues_normalized.json        # Normalized issues
│   ├── raw/                          # Raw reports
│   └── splits/                       # Split reports
│
├── ���️ data/                          # Application Data
│   ├── brushes.json                  # Brush definitions
│   ├── brushes_extra.json            # Extra brushes
│   ├── clients.xml                   # Client configurations
│   ├── menubar.xml                   # Menu bar config
│   ├── memory_guard.json             # Memory limits config
│   │
│   ├── creatures/                    # Creature definitions
│   ├── items/                        # Item definitions
│   └── materials/                    # Material definitions
│
├── ��� Configuration Files (Root)
│   ├── pyproject.toml                # Python project config
│   ├── pytest.ini                    # Pytest config
│   ├── requirements-dev.txt          # Dev dependencies
│   ├── .gitignore                    # Git ignore rules
│   ├── .gitattributes                # Git attributes
│   ├── .editorconfig                 # Editor config
│   ├── .pre-commit-config.yaml       # Pre-commit hooks
│   ├── mypy_report.txt               # Mypy report
│   ├── ruff_report.txt               # Ruff report
│   ├── sonar-project.properties      # SonarQube config
│   ├── vcpkg.json                    # vcpkg dependencies
│   ├── CMakeLists.txt                # CMake config (legacy C++)
│   └── CMakePresets.json             # CMake presets
│
└── ��� Metadata Files
    ├── README.md                     # Project README
    ├── LICENSE                       # License file
    ├── CHANGELOG.md                  # Changelog
    └── .version                      # Version file
```

---

## ��� Layer Dependency Rules

### ✅ Allowed Dependencies

```
vis_layer ──────► logic_layer ──────► core
    │                  │                │
    │                  │                └──► No dependencies
    │                  └──────────────────► core only
    └──────────────────────────────────► core + logic_layer
```

### ❌ Forbidden Dependencies

```
core ──────X──────► logic_layer   # NEVER
core ──────X──────► vis_layer      # NEVER
logic_layer ──X──► vis_layer       # NEVER
```

### Dependency Matrix

| From ↓ / To → | core | logic_layer | vis_layer |
|---------------|------|-------------|-----------|
| **core**      | ✅   | ❌          | ❌        |
| **logic_layer** | ✅   | ✅          | ❌        |
| **vis_layer** | ✅   | ✅          | ✅        |

---

## ��� File Naming Conventions

### Module Names
- **Lowercase with underscores:** `auto_border.py`, `items_xml.py`
- **Singular for single class:** `gamemap.py` (contains `GameMap`)
- **Plural for collections:** `brushes.py` (contains multiple brush types)

### Class Names
- **PascalCase:** `GameMap`, `EditorSession`, `ItemsXML`
- **Descriptive and specific:** `OTBMLoader`, not `Loader`

### Function/Method Names
- **Lowercase with underscores:** `load_map()`, `apply_brush()`
- **Verb-first for actions:** `get_tile()`, `set_item()`, `remove_selection()`

### Constants
- **UPPERCASE with underscores:** `MAX_FILE_SIZE`, `DEFAULT_ZOOM`

### Private Members
- **Single underscore prefix:** `_internal_cache`, `_process_node()`

---

## ��� Module Organization Principles

### 1. Single Responsibility
Each module should have ONE clear purpose:
- ✅ `otbm_loader.py` - Loads OTBM files
- ❌ `utils.py` - Too generic, unclear purpose

### 2. Cohesion
Related functionality stays together:
- ✅ `borders/` directory contains all border-related code
- ❌ Scattering border logic across multiple unrelated files

### 3. Low Coupling
Minimize dependencies between modules:
- ✅ Use protocols/interfaces for dependencies
- ❌ Direct imports of implementation details

### 4. No Circular Dependencies
Never create circular imports:
- ✅ Use protocols, type hints with `TYPE_CHECKING`
- ❌ Module A imports B, B imports A

---

## ��� Best Practices

### Import Order (PEP 8)

```python
# 1. Standard library imports
import sys
from pathlib import Path

# 2. Third-party imports
from PyQt6.QtWidgets import QWidget
import yaml

# 3. Local imports (core)
from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.io.otbm.loader import OTBMLoader

# 4. Local imports (logic_layer)
from py_rme_canary.logic_layer.session.editor import EditorSession

# 5. Local imports (vis_layer) - ONLY in vis_layer files
from py_rme_canary.vis_layer.ui.theme import ThemeManager

# 6. Type-only imports (avoid circular deps)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from py_rme_canary.logic_layer.brushes.base_brush import BaseBrush
```

### Type Hints

```python
from typing import Protocol, Optional, List
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Position:
    """3D position in map space."""
    x: int
    y: int
    z: int

def get_tile(pos: Position) -> Optional[Tile]:
    """Get tile at position, or None if empty."""
    ...
```

### Docstrings (Google Style)

```python
def load_map(path: Path, items_db: ItemsXML) -> GameMap:
    """Load a map from OTBM file.
    
    Args:
        path: Path to .otbm file
        items_db: Loaded items database
    
    Returns:
        Loaded GameMap instance
    
    Raises:
        FileNotFoundError: If map file doesn't exist
        OTBMVersionError: If unsupported OTBM version
    
    Example:
        >>> items = ItemsXML.from_file("items.xml")
        >>> game_map = load_map(Path("map.otbm"), items)
    """
    ...
```

---

## ��� Cleanup Recommendations

### Remove/Deprecate
1. **data_layer/** - Duplicate of core/, should be removed
2. **tk_app.py** - Unmaintained Tkinter UI
3. **brushes.py** - Replaced by brush_definitions.py
4. **auto_border.py** - Replaced by borders/ module
5. **tempCodeRunnerFile.py** - Temporary debug file

### Consolidate
1. **mirroring.py** - Implement or move to geometry.py
2. **map_search.py** - Merge into operations/search.py
3. **map_statistics.py** - Merge into operations/statistics.py

---

## ��� Checklist for New Files

Before creating a new file, ask:

- [ ] Does this belong in core/, logic_layer/, or vis_layer/?
- [ ] Is there an existing module that should contain this?
- [ ] Does this violate layer dependency rules?
- [ ] Is the name clear and follows conventions?
- [ ] Is there a protocol/interface I should use instead?
- [ ] Am I creating a circular dependency?
- [ ] Is this file testable in isolation?

---

## ��� Examples

### ✅ Good Structure

```python
# File: py_rme_canary/logic_layer/brushes/wall_brush.py
"""Wall brush implementation."""

from dataclasses import dataclass
from typing import Protocol

from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.logic_layer.brushes.base_brush import BaseBrush

@dataclass(frozen=True, slots=True)
class WallBrush(BaseBrush):
    """Brush for painting walls with auto-alignment."""
    
    wall_id: int
    
    def apply(self, map: GameMap, x: int, y: int, z: int) -> None:
        """Apply wall to tile with auto-alignment."""
        tile = map.get_or_create_tile(x, y, z)
        # Implementation...
```

### ❌ Bad Structure

```python
# File: py_rme_canary/utils/misc.py (DON'T DO THIS)
"""Miscellaneous utilities."""  # Too vague!

# Mixing concerns
def load_map(...): ...           # Should be in core/io/
def apply_brush(...): ...        # Should be in logic_layer/brushes/
def render_tile(...): ...        # Should be in vis_layer/renderer/
```

---

## ��� Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture overview
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [PRD.md](PRD.md) - Product requirements
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Feature status

---
## 🤖 AI Agent Quick Reference

### Critical Rules for File Creation/Modification

**Before creating ANY file:**
1. Verify layer assignment (core/logic_layer/vis_layer)
2. Check dependency matrix (core ≠> logic/vis, logic ≠> vis)
3. Validate naming convention (lowercase_with_underscores)
4. Ensure no circular dependencies
5. Follow import order (stdlib → third-party → local)

**Forbidden Patterns (AUTO-REJECT):**
- ❌ `from vis_layer import *` in core/ or logic_layer/
- ❌ `utils.py` or `misc.py` without specific purpose
- ❌ Circular imports (A imports B, B imports A)
- ❌ Missing type hints on public functions
- ❌ Bare `except:` clauses

**Mandatory for New Modules:**
- ✅ Module-level docstring (Google style)
- ✅ `__all__` export list
- ✅ Type hints on all functions
- ✅ Corresponding test file in tests/

### Verification Commands
```bash
# Check circular dependencies
pydeps py_rme_canary --show-cycles

# Validate import structure
importlinter --config .importlinter

# Check layer violations
grep -r "from.*vis_layer" py_rme_canary/core/ py_rme_canary/logic_layer/

# Verify naming conventions
find py_rme_canary -name "*[A-Z]*.py" -not -path "*/tests/*"
```

### Quick Decision Matrix

| Scenario | Action |
|----------|--------|
| Adding data model | → core/data/ |
| Adding I/O parser | → core/io/ |
| Adding brush type | → logic_layer/brushes/ |
| Adding UI widget | → vis_layer/ui/ |
| Adding utility | → Find specific module or create in appropriate layer |
| Unsure of location | → ASK in PR, don't guess |

---
**END OF DOCUMENT**
