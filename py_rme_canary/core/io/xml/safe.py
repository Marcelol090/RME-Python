from __future__ import annotations

import importlib
from types import ModuleType
from xml.etree import ElementTree as stdlib_etree

# Provide typed aliases from stdlib for use in annotations.
Element = stdlib_etree.Element
ElementTree = stdlib_etree.ElementTree
ParseError = stdlib_etree.ParseError
SubElement = stdlib_etree.SubElement


def _load_safe_etree() -> ModuleType:
    try:
        mod = importlib.import_module("defusedxml.ElementTree")
        # Ensure standard factory/serialization functions are available on the module
        # even if defusedxml doesn't expose them directly.
        if not hasattr(mod, "Element"):
            setattr(mod, "Element", stdlib_etree.Element)
        if not hasattr(mod, "SubElement"):
            setattr(mod, "SubElement", stdlib_etree.SubElement)
        if not hasattr(mod, "tostring"):
            setattr(mod, "tostring", stdlib_etree.tostring)
        if not hasattr(mod, "ParseError"):
            setattr(mod, "ParseError", stdlib_etree.ParseError)
        return mod
    except ModuleNotFoundError:
        # Fallback to stdlib for trusted local XML inputs when defusedxml is unavailable.
        return stdlib_etree


safe_etree = _load_safe_etree()

__all__ = ["Element", "ElementTree", "ParseError", "SubElement", "safe_etree"]
