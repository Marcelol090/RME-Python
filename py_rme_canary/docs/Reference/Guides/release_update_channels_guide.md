# Release Update Channels Guide

## Purpose

This guide defines how `py_rme_canary` publishes update metadata for desktop clients with safe rollback behavior.

Implemented channels:
- `stable`
- `beta`
- `nightly`

Security baseline:
- SHA-256 checksum is always required.
- Signature is recommended for every channel and required for `stable`.
- Rollback metadata must include the previous known-good version when available.

## Source of Truth

- Channel policy JSON: `py_rme_canary/release/channels.json`
- Channel policy XML: `py_rme_canary/release/update_policy.xml`
- Manifest schema: `py_rme_canary/release/update_manifest.schema.json`
- Manifest generator: `py_rme_canary/tools/release/generate_update_manifest.py`

## CI Workflow

Workflow:
- `.github/workflows/release_update_manifest.yml`

Inputs:
- `channel`: `stable|beta|nightly`
- `version`: release version string
- `base_url`: base URL where binaries are hosted
- `asset_glob`: artifact glob (default `dist/*`)
- `previous_manifest`: optional previous manifest path

Outputs:
- `.quality_reports/release/manifest.<channel>.json`
- `.quality_reports/release/manifest.<channel>.xml`
- `.quality_reports/release/manifest.<channel>.sig` (if cosign key is available)

## Local Generation

```bash
python py_rme_canary/tools/release/generate_update_manifest.py \
  --channel stable \
  --version 1.4.0 \
  --asset dist/map_editor_windows_x64.zip \
  --base-url https://downloads.example.com/rme/stable/1.4.0 \
  --output-json .quality_reports/release/manifest.stable.json \
  --output-xml .quality_reports/release/manifest.stable.xml \
  --previous-manifest .quality_reports/release/manifest.previous.json
```

## Rollback Contract

Each manifest should preserve:
- `rollback.enabled = true`
- `rollback.strategy = keep-last-known-good`
- `rollback.previous_version` when known
- `rollback.previous_manifest_url` when available

Client behavior recommendation:
1. Download manifest for active channel.
2. Verify SHA-256 checksum before install.
3. Verify signature when required.
4. On failure, restore previous version and previous manifest.

## Operational Notes

- Use `stable` only for signed, release-grade binaries.
- Use `beta` for pre-release verification with broader testing.
- Use `nightly` for fast validation and integration feedback.
- Never publish unsigned binaries as `stable`.
