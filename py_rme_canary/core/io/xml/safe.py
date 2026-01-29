from __future__ import annotations

import importlib
from types import ModuleType
from xml.etree import ElementTree as stdlib_etree

# Provide typed aliases from stdlib for use in annotations.
Element = stdlib_etree.Element
ElementTree = stdlib_etree.ElementTree
ParseError = stdlib_etree.ParseError


def _load_safe_etree() -> ModuleType:
    try:
        module = importlib.import_module("defusedxml.ElementTree")
        # Backfill standard ElementTree methods missing in defusedxml
        for attr in ["Element", "SubElement", "tostring"]:
            if not hasattr(module, attr):
                setattr(module, attr, getattr(stdlib_etree, attr))
        return module
    except ModuleNotFoundError:
        # Fallback to stdlib for trusted local XML inputs when defusedxml is unavailable.
        return stdlib_etree


safe_etree = _load_safe_etree()

__all__ = ["Element", "ElementTree", "ParseError", "safe_etree"]
