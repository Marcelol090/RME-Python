"""Experimental/deprecated UI components.

This module contains UI components that are NOT part of the main application.
These files use PySide6 instead of PyQt6 and are kept for reference only.

DO NOT IMPORT FROM THIS MODULE IN PRODUCTION CODE.

Files here:
- dialogs.py: AboutDialog, PropertyDialog (PySide6 prototypes)
- tileset.py: TilesetDialog, AddTilesetDialog (PySide6 prototypes)

The canonical implementations are in:
- vis_layer/ui/main_window/dialogs/ (PyQt6)
"""

import warnings

warnings.warn(
    "py_rme_canary.vis_layer.ui._experimental is deprecated and should not be used.",
    DeprecationWarning,
    stacklevel=2,
)
