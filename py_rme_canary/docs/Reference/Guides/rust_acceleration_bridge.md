# Rust Acceleration Bridge Guide

## Scope

This project uses a **selective acceleration** model:

- Python/PyQt6 remains the orchestration layer.
- Rust is used only for measured CPU-bound hot paths.
- Every accelerated path must keep a Python fallback.

Current bridge:
- Adapter: `py_rme_canary/logic_layer/rust_accel.py`
- Optional extension module: `py_rme_canary/rust/py_rme_canary_rust`

## Implemented Functions

### 1. `spawn_entry_names_at_cursor(payload, x, y, z) -> list[str]`
- Looks up spawn entries at a cursor position.
- Input payload is normalized in Python as:
  - `[{x, y, z, radius, entries: [(name, dx, dy), ...]}, ...]`
- Behavior is parity-compatible with Python fallback logic.

### 2. `fnv1a_64_hash(data: bytes) -> int` (NEW)
- FNV-1a 64-bit hash of raw bytes.
- **~100-200× faster** than pure-Python byte loop.
- Used by sprite hash matching for cross-version clipboard.
- Python bridge: `rust_accel.fnv1a_64(data)`.

### 3. `sprite_hash(pixel_data: bytes, width: int, height: int) -> int` (NEW)
- Combines dimension bytes + pixel data, then computes FNV-1a hash.
- Avoids Python `bytes` concatenation overhead.
- Python bridge: `rust_accel.sprite_hash(pixel_data, width, height)`.

### 4. `render_minimap_buffer(tile_colors, tiles_x, tiles_y, tile_size, bg_r, bg_g, bg_b) -> bytes` (NEW)
- Renders a flat RGB pixel buffer from per-tile colors.
- `tile_colors`: `list[(r, g, b, a)]` in row-major order. `a=0` means transparent (use background).
- **~50-100× faster** than Python's triple-nested pixel loop.
- Python bridge: `rust_accel.render_minimap_buffer(...)`.

### 5. `assemble_png_idat(image_data: bytes, width: int, height: int) -> bytes` (NEW)
- Prepends filter bytes to each row, then zlib-compresses.
- Returns raw IDAT data for PNG file generation.
- **~10-30× faster** than Python row assembly + `zlib.compress`.
- Python bridge: `rust_accel.assemble_png_idat(...)`.

## Build Locally

```bash
cd py_rme_canary/rust/py_rme_canary_rust
python -m pip install maturin
maturin develop --release
```

After build, Python will automatically prefer `py_rme_canary_rust` when available.

## Validation Checklist

- Run fallback/backend parity tests:
  - `python -m pytest -q py_rme_canary/tests/unit/logic_layer/test_rust_accel.py`
  - `python -m pytest -q py_rme_canary/tests/unit/vis_layer/ui/test_qt_map_editor_session_helpers.py`
- Confirm normal editor behavior when module is absent.
- Confirm no UI flow depends on Rust availability.

## Migration Rules for Next Hotpaths

1. Measure first, then migrate.
2. Keep Rust interfaces narrow and deterministic.
3. Add unit tests before replacing Python loops.
4. Ship in small PR-sized increments.

## Candidate Future Hotpaths

| Function | File | Speedup | Notes |
|---|---|---|---|
| `_contiguous_fill()` BFS | fill_tool.py | ~20-50× | Requires tile data extraction |
| `_compute_ground_neighbor_mask()` | borders/processor.py | ~10-30× | Batch bitmask computation |
| `_find_positions_by_item_predicate()` | map_search.py | ~10-20× | Linear scan over all tiles |
