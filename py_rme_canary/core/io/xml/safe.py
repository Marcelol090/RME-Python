from __future__ import annotations

import importlib
from types import ModuleType
from xml.etree import ElementTree as stdlib_etree

# Provide typed aliases from stdlib for use in annotations.
Element = stdlib_etree.Element
SubElement = stdlib_etree.SubElement
ElementTree = stdlib_etree.ElementTree
ParseError = stdlib_etree.ParseError


def _load_safe_etree() -> ModuleType:
    try:
        return importlib.import_module("defusedxml.ElementTree")
    except ModuleNotFoundError:
        # Fallback to stdlib for trusted local XML inputs when defusedxml is unavailable.
        return stdlib_etree


safe_etree = _load_safe_etree()

__all__ = ["Element", "SubElement", "ElementTree", "ParseError", "safe_etree"]
