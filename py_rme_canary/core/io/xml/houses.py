"""Houses XML I/O (new module path).

Kept as a thin wrapper over `core/io/houses_xml.py` for compatibility.
"""

from __future__ import annotations

from py_rme_canary.core.io.houses_xml import (
    build_houses_xml,
    load_houses,
    parse_houses_xml,
    save_houses,
)

__all__ = [
    "build_houses_xml",
    "load_houses",
    "parse_houses_xml",
    "save_houses",
]
