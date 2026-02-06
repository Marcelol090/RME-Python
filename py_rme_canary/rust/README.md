# Rust Acceleration Workspace

This directory contains optional Rust accelerators for `py_rme_canary`.

Principles:

1. Keep PyQt6/UI orchestration in Python.
2. Move only profiled CPU-bound hot paths to Rust.
3. Preserve Python fallback behavior for every accelerated function.
4. Validate parity with unit tests before enabling broader rollout.

Current crate:

- `py_rme_canary_rust` at `py_rme_canary/rust/py_rme_canary_rust`

Build locally:

```bash
cd py_rme_canary/rust/py_rme_canary_rust
python -m pip install maturin
maturin develop --release
```

If the module is not installed, `py_rme_canary/logic_layer/rust_accel.py` automatically uses a pure Python fallback.
