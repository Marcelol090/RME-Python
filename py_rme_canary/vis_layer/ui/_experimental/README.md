# Experimental UI Components

⚠️ **WARNING: DO NOT USE THESE FILES IN PRODUCTION**

This directory contains UI prototypes that were developed using **PySide6**
but are **not compatible** with the main application which uses **PyQt6**.

## Contents

| File | Description | Status |
|------|-------------|--------|
| `dialogs.py` | AboutDialog, PropertyDialog | Deprecated - use PyQt6 versions in `main_window/dialogs/` |
| `tileset.py` | TilesetDialog, AddTilesetDialog | Deprecated - never integrated |

## Why Keep These?

- **Reference**: The code may contain useful logic or UI patterns
- **Migration**: Can be converted to PyQt6 if features are needed
- **History**: Preserves development history

## Migration Path

To use these components in the main application:

1. Change imports from `PySide6` to `PyQt6`
2. Update any PySide6-specific API calls
3. Integrate with the `QtMapEditor` main window
4. Add proper tests

## See Also

- [ARCHITECTURE.md](../../../docs/ARCHITECTURE.md) - Canonical architecture
- [PRD.md](../../../docs/PRD.md) - Product requirements
- [qt_app.py](../../qt_app.py) - Main application entry point
