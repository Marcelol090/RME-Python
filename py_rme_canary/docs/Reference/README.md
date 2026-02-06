# py_rme_canary Reference

`py_rme_canary` is a modern map editor initiative built around a PyQt6-first architecture with optional Rust acceleration for selected hot paths.

## Documentation Entry Points

- Main index: `py_rme_canary/docs/Reference/INDEX.md`
- Product requirements: `py_rme_canary/docs/Reference/PRD.md`
- Quality policy (XML): `py_rme_canary/docs/Reference/quality_pipeline.xml`
- Quality operations guide: `py_rme_canary/docs/Reference/Guides/quality_pipeline_guide.md`
- Jules API integration: `py_rme_canary/docs/Reference/Guides/jules_api_integration.md`
- Rust acceleration bridge: `py_rme_canary/docs/Reference/Guides/rust_acceleration_bridge.md`
- Release channel updates: `py_rme_canary/docs/Reference/Guides/release_update_channels_guide.md`

## Engineering Direction

1. Keep UI/UX orchestration in Python and PyQt6.
2. Move only profiled CPU-bound loops to Rust through narrow interfaces.
3. Maintain deterministic behavior with and without optional accelerators.
4. Enforce checksum-first release manifests and rollback metadata.

## Quality Workflow

Use the quality pipeline before integration:

```bash
./quality.sh --dry-run --skip-libcst --skip-sonarlint
```

For local Jules automation:

```bash
python py_rme_canary/scripts/jules_runner.py --project-root . generate-suggestions
```
