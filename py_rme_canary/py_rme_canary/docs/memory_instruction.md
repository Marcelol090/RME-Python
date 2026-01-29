# Project Memory (Canonical)

This file mirrors active work from the canonical memory file:
`py_rme_canary/docs/memory_instruction.md`

## ACTIVE WORK (auto-updated)

### [2026-01-14] Legacy parity implementation started
- Implemented: mirror drawing refactor in `vis_layer/ui/canvas/widget.py` using shared logic; added unit tests for mirroring.
- Next: implement missing legacy brushes (Wall/Carpet/Table) parity checks and wiring, then start Live collaboration (`live_socket`/`live_peer`) with basic integration.

### [2026-01-14] Wall/Carpet/Table parity update
- Implemented: wall-like neighbor expansion for carpet/table auto-border; added unit tests for carpet/table stacking rules.
- Updated: phase4 verifier keywords to detect wall/carpet/table implementations.
- Next: start Live collaboration base (live_socket/live_peer) and OTMM I/O skeleton.

### [2026-01-14] Live collaboration base (MVP)
- Implemented: LiveSocket + LivePeer base classes; LiveServer now uses LivePeer and broadcasts TILE_UPDATE.
- Implemented: LiveClient now inherits LiveSocket; EditorSession handles TILE_UPDATE without rebroadcast loop.
- Next: implement OTMM saver + roundtrip tests.

### [2026-01-14] OTMM detection + placeholder loader
- Implemented: detect .otmm magic; added OTMM loader entry with explicit error and OTBM fallback for mislabeled files.
- Added: unit tests for map detection and OTMM error path.
- Next: implement OTMM saver + roundtrip tests.

### [2026-01-14] OTMM loader (read)
- Implemented: OTMM constants + NodeFile-based loader for tiles/items/towns/houses/spawns with warnings + memory guard.
- Added: unit test for OTMM tile/item parsing, regression test for legacy U16 house payloads, town/spawn data parsing tests, plus unknown item placeholder + empty node coverage.
- Next: run quality pipeline when env is ready.

### [2026-01-14] OTMM saver (write)
- Implemented: OTMM serializer + atomic save with items/tiles/towns/houses/spawns; aligned house town/rent/beds to legacy U16 and loader accepts U16/U32 house payloads.
- Added: OTMM serialize->load roundtrip unit test.
- Next: run quality pipeline (black/isort/mypy/pytest).

## MEGA TODOs (one-shot backlog)
- Live: port LiveSocket/LivePeer from legacy, wire basic sync into EditorSession, add packet handlers + tests.
- OTMM: add edge-case OTMM coverage (unknown attrs, malformed nodes).
- Render: complete MapDrawer + DrawingOptions layer toggles; minimal OpenGL render path for tiles.
- UI: tileset window wiring + properties dialogs parity; replace remaining PySide6 stubs.
- Search/Replace: advanced search modes + replace on selection parity + results export.
- Cleanup: remove deprecated data_layer and brushes.py (or move to _legacy) with docs update.
- Quality: run quality-pipeline + pytest, fix logs, update CHANGELOG + IMPLEMENTATION_STATUS.
