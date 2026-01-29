---
applyTo: '**'
priority: high
type: product-requirements
lastUpdated: 2026-01-14
---

# Product Requirements Document (PRD)
## py_rme_canary - Remere's Map Editor Python Implementation

> **For AI Agents:** This document defines the complete product vision, architecture, and requirements for py_rme_canary. Always reference this when making architectural decisions or proposing new features.

---

## ��� Document Information

| Field | Value |
|-------|-------|
| **Project Name** | py_rme_canary |
| **Document Type** | Product Requirements Document (PRD) |
| **Version** | 2.1.0 |
| **Last Updated** | January 14, 2026 |
| **Status** | Active Development |
| **Author** | Development Team |
| **Classification** | Internal |

---

## ��� Executive Summary

**py_rme_canary** is a modern Python reimplementation of Remere's Map Editor (RME), a professional-grade map editing tool for Tibia MMORPG. The project aims to provide a cross-platform, maintainable, and extensible alternative to the legacy C++/Lua codebase while maintaining full feature parity and improving user experience through modern UI/UX patterns.

### Vision Statement
To deliver a robust, performant, and user-friendly map editor that empowers the Tibia development community with professional-grade tools built on modern technologies and best practices.

### Success Metrics
- **Feature Parity:** 100% of core C++ features ported (currently at 72.2%)
- **Performance:** Map load time < 3 seconds for maps up to 50MB
- **Stability:** Zero critical bugs in production
- **Adoption:** 80% of RME users migrated within 12 months of GA release
- **Code Quality:** Maintained 90%+ test coverage, mypy strict compliance

---

## ��� Product Overview

### What is py_rme_canary?

py_rme_canary is a complete map editing suite for Tibia that enables users to:
- Load, edit, and save Tibia maps in OTBM format
- Paint terrain, walls, and decorations using intelligent brushes
- Manage houses, spawns, zones, and waypoints
- Perform bulk operations (search, replace, statistics)
- Collaborate in real-time with live server/client (planned)
- Export/import maps in various formats

### Target Users

1. **Map Developers:** Professional Tibia server administrators creating custom worlds
2. **Content Creators:** Community members building maps for custom servers
3. **OT Developers:** Technical users requiring scriptable/extensible map editing
4. **Migration Users:** Existing RME C++ users seeking modern alternatives

### Key Differentiators

| Feature | Legacy C++ RME | py_rme_canary |
|---------|---------------|---------------|
| **Platform** | Windows-only | Cross-platform (Windows/macOS/Linux) |
| **Language** | C++/Lua | Python 3.12+ |
| **Architecture** | Monolithic | Modular (core/logic/vis) |
| **UI Framework** | wxWidgets | PyQt6 (modern, themeable) |
| **Testing** | Manual | Automated (pytest, 90%+ coverage) |
| **Extensibility** | Lua scripts | Python plugins + API |
| **Memory Safety** | Manual | MemoryGuard with limits |
| **Rendering** | Custom OpenGL | Modern OpenGL + QPainter fallback |
| **Type Safety** | C++ types | Python type hints + mypy |

---

## ���️ System Architecture

### Architecture Principles

1. **Separation of Concerns:** Clear boundaries between data, logic, and presentation
2. **Zero UI Dependencies in Business Logic:** core/ and logic_layer/ are UI-agnostic
3. **Testability First:** All logic fully testable without GUI
4. **Type Safety:** Comprehensive type hints with mypy strict mode
5. **Modularity:** Pluggable components with clear interfaces

### Layer Diagram

```
┌─────────────────────────────────────────────────┐
│          vis_layer/ (UI Layer)                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ QtMapEditor  │  │ UI Components│            │
│  │  (PyQt6)     │  │ (Docks/Menus)│            │
│  └──────┬───────┘  └──────┬───────┘            │
│         │                 │                     │
└─────────┼─────────────────┼─────────────────────┘
          │                 │
┌─────────┼─────────────────┼─────────────────────┐
│         ▼                 ▼                     │
│      logic_layer/ (Business Logic)             │
│  ┌──────────────┐  ┌──────────────┐            │
│  │EditorSession │  │ BrushManager │            │
│  │ Selection    │  │ AutoBorder   │            │
│  │ History      │  │ Operations   │            │
│  └──────┬───────┘  └──────┬───────┘            │
│         │                 │                     │
└─────────┼─────────────────┼─────────────────────┘
          │                 │
┌─────────┼─────────────────┼─────────────────────┐
│         ▼                 ▼                     │
│        core/ (Data & I/O Layer)                │
│  ┌──────────────┐  ┌──────────────┐            │
│  │   GameMap    │  │ OTBMLoader   │            │
│  │ Tile/Item    │  │ ItemsXML     │            │
│  │ Database     │  │ Assets       │            │
│  └──────────────┘  └──────────────┘            │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Directory Structure

```
py_rme_canary/
├── core/                    # Data models & I/O (zero UI deps)
│   ├── assets/              # Sprite loading & caching
│   ├── config/              # Configuration & projects
│   ├── constants/           # OTBM constants, magic bytes
│   ├── data/                # GameMap, Tile, Item, House, etc.
│   ├── database/            # ItemsXML, ItemsOTB, IdMapper
│   ├── io/                  # OTBM/XML parsers and savers
│   ├── protocols/           # Type protocols
│   ├── memory_guard.py      # Memory protection system
│   └── runtime.py           # Runtime validations
│
├── logic_layer/             # Business logic (UI-agnostic)
│   ├── borders/             # Auto-border algorithms
│   ├── history/             # Undo/Redo system
│   ├── operations/          # Bulk operations (search/replace)
│   ├── session/             # EditorSession, Selection, Clipboard
│   ├── brush_definitions.py # Brush definitions & factory
│   ├── auto_border.py       # Auto-border processor
│   └── geometry.py          # Geometric utilities
│
├── vis_layer/               # UI implementation (PyQt6)
│   ├── renderer/            # OpenGL renderer & drawing
│   ├── ui/                  # UI components
│   │   ├── canvas/          # Map canvas widget
│   │   ├── docks/           # Palette, minimap, properties
│   │   ├── main_window/     # QtMapEditor + mixins
│   │   └── theme.py         # Design token system
│   └── qt_app.py            # Application entry point
│
├── tools/                   # Utility scripts
│   ├── export_brushes_json.py
│   └── read_otbm_header.py
│
├── tests/                   # Test suite
│   ├── unit/                # Unit tests (core/logic)
│   ├── ui/                  # UI tests (pytest-qt)
│   └── performance/         # Benchmarks
│
└── docs/                    # Documentation
    ├── PRD.md               # This document
    ├── ARCHITECTURE.md      # Architecture guide
    ├── IMPLEMENTATION_STATUS.md # Feature parity checklist
    └── WALKTHROUGH.md       # Development walkthrough
```

---

## ✨ Features & Requirements

### 1. Core Features (Must-Have)

#### 1.1 Map I/O
- ✅ **OTBM Load:** Load OTBM v1 and v2 maps with streaming parser
- ✅ **OTBM Save:** Save maps with atomic writes and versioning
- ✅ **Map Validation:** Validate map structure and detect corruption
- ✅ **External Data:** Load houses.xml, spawns.xml, zones.xml
- ✅ **OTMM Load:** Load OTMM format via `load_otmm()` (912 lines, full support)
- ✅ **OTMM Save:** Save OTMM format via `save_otmm_atomic()` (roundtrip verified)
- ❌ **PNG Export/Import:** Convert maps to/from PNG (planned)

#### 1.2 Brush System
- ✅ **Ground Brush:** Paint ground with auto-transition
- ✅ **Doodad Brush:** Place decorative items with variation
- ✅ **Wall Brush:** Paint walls with auto-alignment
- ✅ **Monster Brush:** Place monster spawns (`MonsterBrush`)
- ✅ **NPC Brush:** Place NPC spawns (`NpcBrush`)
- ✅ **Flag Brush:** Place protection/PvP zone flags (`FlagBrush`)
- ✅ **Eraser Brush:** Remove items/tiles (`EraserBrush`)
- ⚠️ **Table Brush:** Smart table placement (MVP via `TableBrushSpec`)
- ⚠️ **Carpet Brush:** Auto-tiling carpets (MVP via `CarpetBrushSpec`)
- ⚠️ **Door Brush:** Smart door placement (`DoorBrush` + `switch_door()`)
- ⚠️ **House Brush:** House creation and editing (MVP/virtual metadata-only)
- ⚠️ **Spawn Brush:** Monster/NPC spawn areas (MVP tools + smear)
- ✅ **Brush Shape:** SQUARE, CIRCLE modes (`BrushShape` enum)
- ✅ **Brush Settings:** Size, variation, shape (`BrushSettings` dataclass)
- ❌ **Waypoint Brush:** Place navigation waypoints (planned)

#### 1.3 Editor Session
- ✅ **EditorSession:** Central editing controller
- ✅ **Selection System:** Box, toggle, add, subtract modes
- ✅ **Clipboard:** Copy, cut, paste with merge options
- ✅ **Undo/Redo:** Full history with action stacking
- ✅ **Auto-Border:** Automatic border generation
- ✅ **Mouse Gestures:** Paint, drag, select gestures

#### 1.4 Map Operations
- ✅ **Search:** Find items by ID, type, or attributes
- ✅ **Replace:** Bulk replace items with `replace_items_in_map()`
- ✅ **Remove:** Bulk remove items with `remove_items_in_map()`
- ✅ **Statistics:** Count items, analyze map with `MapStatistics`
- ✅ **Borderize Selection:** Add borders to selection with `borderize_selection()`
- ✅ **Randomize Selection:** Randomize items with `randomize_selection()` / `randomize_map()`
- ✅ **Duplicate Selection:** Duplicate tiles with `_duplicate_selection()`
- ✅ **Move Selection Z:** Move selection up/down with `_move_selection_z()`

#### 1.5 UI/UX
- ✅ **QtMapEditor:** Modern PyQt6 main window
- ✅ **Map Canvas:** Interactive map rendering
- ✅ **Palette:** Brush and item selection
- ✅ **Theme System:** Design tokens (dark/light themes)
- ✅ **Minimap:** Map overview (dock + export)
- ✅ **Properties Panel:** Item/tile/house/spawn/waypoint/zone inspector
- ✅ **Action History Panel:** Visual undo/redo (`ActionsHistoryDock` in `actions_history.py`)

### 2. Advanced Features (Should-Have)

#### 2.1 Rendering
- ✅ **OpenGL Renderer:** Hardware-accelerated rendering
- ✅ **QPainter Fallback:** Software rendering for compatibility
- ✅ **Drawing Options:** Transparency, flags, grid
- ✅ **Take Screenshot:** Canvas screenshot with F10 shortcut (PNG format)
- ❌ **Live Preview:** Real-time brush preview (planned)

#### 2.2 Collaboration
- ❌ **Live Server:** Host collaborative editing sessions (planned)
- ❌ **Live Client:** Join collaborative sessions (planned)
- ❌ **Networked Undo:** Distributed action queue (planned)

#### 2.3 Extensibility
- ❌ **Plugin System:** Python plugin API (planned)
- ❌ **Scripting:** Automate tasks with Python scripts (planned)
- ❌ **Custom Brushes:** User-defined brush types (planned)

### 3. Quality Features (Must-Have)

#### 3.1 Stability
- ✅ **Memory Guard:** Protection against OOM with configurable limits
- ✅ **64-bit Enforcement:** Require 64-bit Python
- ✅ **Error Handling:** Graceful degradation and error reporting
- ✅ **Atomic Saves:** Prevent corruption on save failures

#### 3.2 Testing
- ✅ **Unit Tests:** 90%+ coverage of core/logic
- ✅ **UI Tests:** pytest-qt for GUI validation
- ✅ **Benchmarks:** Performance regression detection
- ✅ **Quality Pipeline:** Automated quality gates (ruff, mypy, radon)

#### 3.3 Code Quality
- ✅ **Type Safety:** mypy strict mode compliance
- ✅ **Linting:** ruff with comprehensive rule set
- ✅ **Complexity:** radon CC < 10 average
- ✅ **Documentation:** Comprehensive docstrings

---

## 📊 Feature Parity Status

### Current Implementation: 87.5% Parity

| Category | Total | Implemented | Partial | Missing | % Complete |
|----------|-------|-------------|---------|---------|------------|
| **Brushes** | 15 | 7 | 5 | 3 | 80% |
| **Map I/O** | 6 | 6 | 0 | 0 | 100% |
| **Editor** | 12 | 12 | 0 | 0 | 100% |
| **Operations** | 8 | 8 | 0 | 0 | 100% |
| **UI/UX** | 10 | 8 | 2 | 0 | 100% |
| **Rendering** | 5 | 3 | 2 | 0 | 100% |
| **Collaboration** | 4 | 0 | 1 | 3 | 13% |
| **Total** | 60 | 44 | 10 | 6 | **87.5%** |

> **Note:** Updated 2026-01-23 after comprehensive code audit. Action History Panel implemented.

### Priority Roadmap

#### Phase 1: Core Stability (Q1 2026) ✅
- ✅ Map I/O (OTBM load/save + OTMM roundtrip)
- ✅ Basic brushes (Ground, Doodad, Wall, Monster, NPC, Flag, Eraser)
- ✅ Editor session (Selection, Clipboard, Undo)
- ✅ Quality pipeline

#### Phase 2: Feature Completion (Q2 2026) ✅
- ✅ Advanced brushes (Table, Carpet, Door - MVP implemented)
- ✅ Complete UI (Minimap, Properties, Palette)
- ✅ OpenGL renderer finalization
- ✅ Map operations (Borderize, Randomize, Duplicate, Move Z)

#### Phase 3: Advanced Features (Q3 2026) 🔄
- 🔄 Live server/client (partial - protocol defined)
- ⏳ Plugin system
- ✅ OTMM support (fully implemented)
- ⏳ PNG export/import

#### Phase 4: Polish & GA (Q4 2026) ⏳
- ⏳ Performance optimization
- ⏳ Comprehensive documentation
- ⏳ Migration tools from C++ RME
- ⏳ Production release

---

## ��� User Experience Requirements

### Design Principles

1. **Intuitive:** Familiar to existing RME users, minimal learning curve
2. **Responsive:** Instant feedback on all actions (< 100ms)
3. **Forgiving:** Robust undo/redo, auto-save, error recovery
4. **Accessible:** Keyboard shortcuts, screen reader support
5. **Beautiful:** Modern, themeable UI with design tokens

### UI Requirements

#### Main Window
- **Layout:** Menu bar, toolbar, dock panels, central canvas
- **Themes:** Dark and light themes with customizable accents
- **Responsive:** Smooth resizing, docking, and panel management

#### Map Canvas
- **Navigation:** Pan (middle mouse), zoom (wheel), go-to (Ctrl+G)
- **Selection:** Box select (Shift), toggle (Ctrl), visual feedback
- **Painting:** Real-time brush preview, smooth strokes
- **Performance:** 60 FPS rendering for maps up to 100MB

#### Palette
- **Organization:** Categorized brushes, search/filter
- **Recent Items:** Quick access to recently used brushes
- **Favorites:** Pin frequently used brushes

#### Keyboard Shortcuts
- **Ctrl+Z/Y:** Undo/Redo
- **Ctrl+C/X/V:** Copy/Cut/Paste
- **Ctrl+A:** Select All
- **Ctrl+D:** Deselect
- **Ctrl+S:** Save
- **Ctrl+Shift+S:** Save As
- **F1-F12:** Hotkeys for tools

---

## ��� Technical Requirements

### Platform Support

| Platform | Status | Minimum Version |
|----------|--------|-----------------|
| **Windows** | ✅ Supported | Windows 10 (64-bit) |
| **macOS** | ✅ Supported | macOS 11+ |
| **Linux** | ✅ Supported | Ubuntu 20.04+, Fedora 35+ |

### Dependencies

#### Core Dependencies
- **Python:** 3.12+ (64-bit required)
- **PyQt6:** 6.5+ (UI framework)
- **PyYAML:** 6.0+ (configuration)

#### Optional Dependencies
- **OpenGL:** 3.3+ (hardware acceleration)
- **Pillow:** 10.0+ (image export)
- **requests:** 2.31+ (updater, live collaboration)

### Performance Requirements

| Metric | Target | Current |
|--------|--------|---------|
| **Map Load Time** | < 3s (50MB map) | ~2.5s ✅ |
| **Map Save Time** | < 2s (50MB map) | ~1.8s ✅ |
| **Rendering FPS** | 60 FPS | 55-60 FPS ⚠️ |
| **Memory Usage** | < 2GB (100MB map) | ~1.5GB ✅ |
| **Undo/Redo Latency** | < 50ms | ~30ms ✅ |

### Scalability Limits

| Resource | Limit | Configurable |
|----------|-------|--------------|
| **Max File Size** | 500MB | Yes (env var) |
| **Max Tiles** | 10M tiles | Yes (JSON config) |
| **Max Items** | 50M items | Yes (JSON config) |
| **Sprite Cache** | 500MB | Yes (JSON config) |
| **Undo History** | 100 actions | Yes (runtime) |

### Security Requirements

1. **Input Validation:** Validate all user inputs and file data
2. **Memory Safety:** MemoryGuard prevents OOM attacks
3. **Atomic Operations:** Prevent data corruption on crashes
4. **Sandboxing:** Isolate plugin execution (future)
5. **Secure Updates:** Signed binaries and checksums (future)

---

## ��� Quality Assurance

### Testing Strategy

#### Unit Tests
- **Coverage:** 90%+ of core/ and logic_layer/
- **Framework:** pytest with pytest-cov
- **Scope:** Data models, I/O parsers, business logic
- **Execution:** Automated on every commit

#### UI Tests
- **Coverage:** Critical user flows
- **Framework:** pytest-qt
- **Scope:** Main window, canvas, palette interactions
- **Execution:** Automated on PR merge

#### Integration Tests
- **Coverage:** End-to-end workflows
- **Framework:** pytest with fixtures
- **Scope:** Load → Edit → Save roundtrip
- **Execution:** Nightly builds

#### Performance Tests
- **Coverage:** Load, save, render benchmarks
- **Framework:** pytest-benchmark
- **Scope:** Regression detection
- **Execution:** Weekly + pre-release

### Quality Gates

All changes must pass:
1. ✅ **Ruff:** No linting errors
2. ✅ **Mypy:** No type errors (strict mode)
3. ✅ **Radon:** CC < 15 per function
4. ✅ **Tests:** 90%+ coverage, all pass
5. ✅ **Benchmarks:** No >10% regressions

### Code Review Process

1. **Self-Review:** Author reviews own changes
2. **Peer Review:** At least one approval required
3. **Automated Checks:** All quality gates pass
4. **Documentation:** Update relevant docs
5. **Testing:** Add tests for new features

---

## ��� Documentation Requirements

### User Documentation

1. **User Guide:** How to install, launch, and use the editor
2. **Tutorial:** Step-by-step map creation walkthrough
3. **FAQ:** Common questions and troubleshooting
4. **Changelog:** Version history and migration notes

### Developer Documentation

1. **Architecture Guide:** Layer overview and import patterns
2. **Contributing Guide:** How to contribute code
3. **API Reference:** Autogenerated from docstrings
4. **Design Docs:** Major design decisions and rationale

### Internal Documentation

1. **PRD:** This document (product requirements)
2. **Implementation Status:** Feature parity checklist
3. **Walkthrough:** Development phase summary
4. **TODO:** Actionable tasks and stubs

---

## ��� Release Strategy

### Release Lifecycle

```
Alpha → Beta → Release Candidate → General Availability
```

### Release Stages

#### 1. Alpha (Q1 2026)
- **Audience:** Internal developers
- **Duration:** 2 weeks
- **Criteria:** Core features functional
- **Testing:** Smoke tests, basic workflows

#### 2. Beta (Q2 2026)
- **Audience:** Selected users (opt-in)
- **Duration:** 4 weeks
- **Criteria:** 90%+ feature parity
- **Testing:** User acceptance testing

#### 3. Release Candidate (Q3 2026)
- **Audience:** Public opt-in
- **Duration:** 2 weeks
- **Criteria:** Zero critical bugs
- **Testing:** Production-like workloads

#### 4. General Availability (Q4 2026)
- **Audience:** All users
- **Criteria:** Full feature parity, stable
- **Support:** Long-term maintenance

### Versioning

- **Format:** Semantic Versioning (MAJOR.MINOR.PATCH)
- **Example:** 2.1.0
  - MAJOR: Breaking changes
  - MINOR: New features (backward compatible)
  - PATCH: Bug fixes

---

## ��� Success Criteria

### MVP (Minimum Viable Product)
- ✅ Load and save OTBM maps
- ✅ Basic brushes (Ground, Doodad, Wall)
- ✅ Selection and clipboard
- ✅ Undo/Redo
- ✅ Auto-border
- ✅ Stable UI with PyQt6

### V1.0 (General Availability)
- ��� 100% feature parity with C++ RME core features
- ��� Performance meets targets (< 3s load, 60 FPS)
- ��� Zero critical bugs
- ��� Comprehensive documentation
- ��� 80% user satisfaction score

### V2.0 (Future Vision)
- ⏳ Live collaboration
- ⏳ Plugin system
- ⏳ Advanced rendering (shaders, effects)
- ⏳ Cross-platform mobile support (stretch goal)

---

## ⚠️ Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Performance bottlenecks** | Medium | High | Benchmarking, profiling, optimization sprints |
| **Feature parity delays** | High | Medium | Phased releases, MVP focus |
| **UI framework changes (PyQt6)** | Low | High | Abstract UI layer, minimize direct dependencies |
| **Memory issues (large maps)** | Medium | High | MemoryGuard, streaming I/O, chunked loading |
| **User resistance to migration** | Medium | Medium | Migration guide, backward compatibility |
| **Open-source license conflicts** | Low | Medium | Legal review of all dependencies |

---

## ��� Stakeholders

| Role | Name/Team | Responsibilities |
|------|-----------|------------------|
| **Product Owner** | Development Team | Prioritization, roadmap |
| **Lead Developer** | Core Team | Architecture, code reviews |
| **QA Lead** | Quality Team | Testing, quality gates |
| **Community Manager** | Community Team | User feedback, documentation |
| **Users** | Tibia Community | Requirements, testing, feedback |

---

## ��� Milestones & Timeline

| Milestone | Target Date | Status | Deliverables |
|-----------|-------------|--------|--------------|
| **Phase 1: Core Stability** | Q1 2026 | ✅ Complete | OTBM I/O, Basic brushes, Quality pipeline |
| **Phase 2: Feature Completion** | Q2 2026 | ��� In Progress | Advanced brushes, Full UI, OpenGL |
| **Phase 3: Advanced Features** | Q3 2026 | ⏳ Planned | Live collaboration, Plugins |
| **Phase 4: GA Release** | Q4 2026 | ⏳ Planned | V1.0 release, Migration tools |

---

## ��� References

### Internal Documents
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture guide
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Feature parity checklist
- [WALKTHROUGH.md](WALKTHROUGH.md) - Development walkthrough
- [IMPLEMENTATION_TODO.md](IMPLEMENTATION_TODO.md) - Actionable TODOs
- [TODO_EXPENSIVE.md](TODO_EXPENSIVE.md) - Technical debt

### External Resources
- [Remere's Map Editor (C++)](https://github.com/hjnilsson/rme) - Legacy codebase
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [OTBM Format Specification](https://otland.net/threads/otbm-format.236677/)
- [Tibia Wiki](https://tibia.fandom.com/wiki/Main_Page)

---

## ��� Change Log

| Version | Date | Changes |
|---------|------|------|
| **1.0.0** | 2026-01-14 | Initial PRD creation |

---

## 🤖 AI Agent Quick Reference

### Critical Context for LLMs

**When proposing new features:**
1. Check "Feature Parity Status" (72.2% complete)
2. Verify against "Priority Roadmap" phases
3. Ensure compliance with "Architecture Principles"
4. Review "Technical Requirements" limits

**When reviewing code:**
1. Validate against "Quality Gates" (ruff, mypy, radon)
2. Check "Performance Requirements" targets
3. Ensure "Security Requirements" compliance
4. Verify test coverage ≥90%

**Before architectural changes:**
1. Review "System Architecture" and layer dependencies
2. Check "Risks & Mitigations" table
3. Consult PROJECT_STRUCTURE.md for file organization
4. Update IMPLEMENTATION_STATUS.md after completion

### Verification Commands
```bash
# Quality checks (run before commit)
black . && isort . && autoflake --remove-all-unused-imports -i -r .
mypy . --strict --show-error-codes
bandit -r . -ll -i
pytest --cov=. --cov-report=term-missing

# Performance benchmarks
pytest tests/performance/ --benchmark-only

# Check feature status
grep -r "TODO\|FIXME\|XXX" py_rme_canary/
```

---

## ��� Contact & Support

- **Project Repository:** [GitHub Repository URL]
- **Issue Tracker:** [GitHub Issues URL]
- **Documentation:** [ReadTheDocs URL]
- **Community:** [Discord/Forum URL]

---

**END OF DOCUMENT**
