# Client Data Loading Guide

## Goal
Provide a deterministic and user-friendly loading workflow for:
- Sprite assets (`.spr/.dat` or modern `assets/` catalog),
- Appearance metadata (`appearances.dat`),
- Item mappings (`items.otb`),
- Item metadata (`items.xml`).

## UI Entry Points

1. **Assets -> Load Client Data...**
   Opens the integrated loader dialog with staged progress and summary.

2. **Assets -> Set Assets Directory...**
   Quick path selection for assets only, using automatic definition resolution.

3. **Assets -> Load appearances.dat... / Unload appearances.dat**
   Manual appearance metadata override for modern profiles.

## Resolution Priority

When explicit definition files are not provided:

1. `data/<client_version>/items.otb` and `data/<client_version>/items.xml`
2. `data/<engine>/items.otb` and `data/<engine>/items.xml`
3. `data/<engine>/items/items.otb` and `data/<engine>/items/items.xml`
4. `data/items/items.otb` and `data/items/items.xml`

When explicit paths are provided in the loader dialog:
- Explicit files take precedence over auto-detection.
- If `items.otb` is unavailable but `items.xml` is valid, XML mapping fallback is applied.

## Interactive Loading Stages

The integrated loader executes:

1. Detect profile (`modern` vs `legacy`).
2. Load sprite/appearance sources.
3. Load `items.otb` / `items.xml` mappings.
4. Refresh UI synchronization (palette, canvas, preview).
5. Emit completion summary (or status-bar only in silent mode).

## Map Open Progress

`File -> Open...` now exposes progress stages:

1. Detect map format.
2. Parse and translate IDs.
3. Initialize editor session.
4. Apply detected context (engine/version/assets).
5. Finalize project metadata and refresh viewport.

## Troubleshooting

### Sprites do not render
- Verify the loaded profile kind matches the selected client assets.
- Check whether `ID mappings` are present in the completion summary.
- For modern clients, verify `appearances.dat` availability in summary.

### Items display with generic labels only
- Confirm `items.xml` was loaded (explicitly or auto-detected).
- If auto-detection fails, provide explicit `items.xml` in **Load Client Data...**.

### Client path selected but load fails
- Ensure the selected folder is either:
  - a client root containing `assets/` or `.dat/.spr`, or
  - a direct `assets/` folder with `catalog-content.json`.

### Legacy assets with modern map context
- Use explicit `items.otb` / `items.xml` from the target version to keep mapper consistency.

## Best Practice

For reproducible team workflows:
1. Create a dedicated client profile per target version.
2. Use **Load Client Data...** with explicit definition files when working across mixed distributions.
3. Keep `data/<version>/items.otb` and `data/<version>/items.xml` aligned with your server branch.
