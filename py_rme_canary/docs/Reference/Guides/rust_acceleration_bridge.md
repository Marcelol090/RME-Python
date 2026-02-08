# Rust Acceleration Bridge Guide

## Scope

This project uses a **selective acceleration** model:

- Python/PyQt6 remains the orchestration layer.
- Rust is used only for measured CPU-bound hot paths.
- Every accelerated path must keep a Python fallback.

Current bridge:
- Adapter: `py_rme_canary/logic_layer/rust_accel.py`
- Optional extension module: `py_rme_canary/rust/py_rme_canary_rust`

## Implemented Function

- `spawn_entry_names_at_cursor(payload, x, y, z) -> list[str]`
  - Input payload is normalized in Python as:
    - `[{x, y, z, radius, entries: [(name, dx, dy), ...]}, ...]`
  - Behavior is parity-compatible with Python fallback logic.

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
