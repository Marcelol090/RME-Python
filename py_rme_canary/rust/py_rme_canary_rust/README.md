# py_rme_canary_rust

Optional Rust extension module used by `py_rme_canary.logic_layer.rust_accel`.

Current exported function:

- `spawn_entry_names_at_cursor(payload, x, y, z) -> list[str]`

Build locally with `maturin`:

```bash
cd py_rme_canary/rust/py_rme_canary_rust
python -m pip install maturin
maturin develop --release
```

The Python runtime keeps a built-in fallback path, so the editor works even when this module is not installed.
