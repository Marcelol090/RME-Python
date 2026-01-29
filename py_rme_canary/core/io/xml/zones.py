"""Zones XML I/O (new module path).

Kept as a thin wrapper over `core/io/zones_xml.py` for compatibility.
"""

from __future__ import annotations

from py_rme_canary.core.io.zones_xml import build_zones_xml, load_zones, parse_zones_xml, save_zones

__all__ = [
    "build_zones_xml",
    "load_zones",
    "parse_zones_xml",
    "save_zones",
]
