# Planning Documentation Index

> Last updated: 2026-02-10 (session: planning sync + automation path fixes + parity/audit refresh)

## 📁 Directory Structure

```
Planning/
├── INDEX.md              ← You are here
├── Features.md           ← Implementation tracking (85KB)
├── project_tasks.json    ← Prioritized backlog
├── roadmap.json          ← Project roadmap
│
├── TODOs/                ← Task lists by date
│   ├── TODO_CPP_PARITY_UIUX_2026-02-06.md
│   ├── TODO_DEEP_SEARCH_IMPLEMENTATION_2026-02-05.md
│   └── TODO_FRIENDS_JULES_WORKFLOW_2026-02-06.md
│
├── Audits/               ← Gap analysis & audits
│   ├── GAP_ANALYSIS.md
│   ├── GAP_ANALYSIS_2026.md
│   └── DEEP_AUDIT_INTEGRATION_2026-02-08.md
│
└── Guides/               ← Technical guides
    ├── awesome_rust_libraries_guide.md
    └── map_editor_advanced_optimizations.md
```

---

## 📋 Quick Links

### Core Documents

| Document                                   | Description                                  |
| ------------------------------------------ | -------------------------------------------- |
| [Features.md](./Features.md)               | Implementation tracking with tasklist format |
| [project_tasks.json](./project_tasks.json) | JSON backlog with priorities                 |
| [roadmap.json](./roadmap.json)             | Project milestones                           |

### TODOs

| Document                                                             | Focus                 |
| -------------------------------------------------------------------- | --------------------- |
| [CPP Parity UIUX](./TODOs/TODO_CPP_PARITY_UIUX_2026-02-06.md)        | C++ feature parity    |
| [Deep Search](./TODOs/TODO_DEEP_SEARCH_IMPLEMENTATION_2026-02-05.md) | Search implementation |
| [Jules Workflow](./TODOs/TODO_FRIENDS_JULES_WORKFLOW_2026-02-06.md)  | Jules integration     |

### Audits

| Document                                                    | Focus                |
| ----------------------------------------------------------- | -------------------- |
| [GAP_ANALYSIS.md](./Audits/GAP_ANALYSIS.md)                 | Feature gap analysis |
| [GAP_ANALYSIS_2026.md](./Audits/GAP_ANALYSIS_2026.md)       | 2026 gap updates     |
| [Deep Audit](./Audits/DEEP_AUDIT_INTEGRATION_2026-02-08.md) | Integration audit    |

### Guides

| Document                                                                | Focus             |
| ----------------------------------------------------------------------- | ----------------- |
| [Rust Libraries](./Guides/awesome_rust_libraries_guide.md)              | Rust acceleration |
| [Advanced Optimizations](./Guides/map_editor_advanced_optimizations.md) | Performance       |

---

## 🎯 Current Priorities

1. ~~**High**: Strict Quality Hardening~~ ✅ mypy --strict clean on all 373 source files
2. ~~**Medium**: Rust Acceleration expansion~~ ✅ 5 accelerated functions with Python fallbacks
3. ~~**Medium**: In-Game Preview Phase 8 polish & Phase 9 release~~ ✅ Release infrastructure complete
4. ~~**Low**: Live Collaboration v3.0 finalization~~ ✅ Complete

### Recently Completed (2026-02-10)

- ✅ **Phase 9 Release**: Version management (`core/version.py`), auto-update checker, startup splash screen
- ✅ Enhanced build script with Windows version resource injection
- ✅ Release manifest generator (`tools/release.py`) with SHA-256 checksums
- ✅ 71 new tests (918 total), 373 files mypy --strict clean
- ✅ pyproject.toml version bumped to 3.0.0

### Previously Completed (2026-02-09)

- ✅ Lua Monster Import (Revscript) → `core/io/lua_creature_import.py`
- ✅ Sprite Hash Matching (FNV-1a) → `logic_layer/cross_version/sprite_hash.py`
- ✅ Appearances.dat full support (flags/properties) → `core/assets/appearances_dat.py`
- ✅ BorderBuilder custom rule editing → `vis_layer/ui/dialogs/border_builder_dialog.py`
- ✅ Modern Palette Dock legacy API compatibility
- ✅ Asset mapping merge strategy (OTB + XML)
- ✅ mypy --strict clean (367 files: core 91 + logic_layer 96 + vis_layer 180)
- ✅ Rust Acceleration expansion (FNV-1a hash, sprite hash, minimap buffer, PNG IDAT)
