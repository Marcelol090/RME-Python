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
        return importlib.import_module("defusedxml.ElementTree")
    except ModuleNotFoundError:
        # Fallback to stdlib for trusted local XML inputs when defusedxml is unavailable.
        return stdlib_etree


safe_etree = _load_safe_etree()

# Ensure that 'Element' and 'SubElement' are available on the safe_etree module interface
# because defusedxml doesn't expose them directly, but downstream code often expects `ET.Element`.
if not hasattr(safe_etree, "Element"):
    setattr(safe_etree, "Element", stdlib_etree.Element)
if not hasattr(safe_etree, "SubElement"):
    setattr(safe_etree, "SubElement", stdlib_etree.SubElement)
if not hasattr(safe_etree, "tostring"):
    setattr(safe_etree, "tostring", stdlib_etree.tostring)

__all__ = ["Element", "ElementTree", "ParseError", "safe_etree"]
