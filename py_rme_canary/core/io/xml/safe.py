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
        return importlib.import_module("defusedxml.ElementTree")
    except ModuleNotFoundError:
        # Fallback to stdlib for trusted local XML inputs when defusedxml is unavailable.
        return stdlib_etree


safe_etree = _load_safe_etree()

# defusedxml.ElementTree intentionally omits some constructors (Element/SubElement)
# that the rest of the codebase expects. When those attributes are missing,
# borrow the safe stdlib equivalents so code (and tests) can create XML trees.
if not hasattr(safe_etree, "Element"):
    safe_etree.Element = stdlib_etree.Element  # type: ignore[attr-defined]
if not hasattr(safe_etree, "ElementTree"):
    safe_etree.ElementTree = stdlib_etree.ElementTree  # type: ignore[attr-defined]
if not hasattr(safe_etree, "SubElement"):
    safe_etree.SubElement = stdlib_etree.SubElement  # type: ignore[attr-defined]
if not hasattr(safe_etree, "tostring"):
    safe_etree.tostring = stdlib_etree.tostring  # type: ignore[attr-defined]
if not hasattr(safe_etree, "indent") and hasattr(stdlib_etree, "indent"):
    safe_etree.indent = stdlib_etree.indent  # type: ignore[attr-defined]

# Export parse and fromstring from safe_etree
parse = safe_etree.parse
fromstring = safe_etree.fromstring

__all__ = ["Element", "ElementTree", "ParseError", "SubElement", "safe_etree", "parse", "fromstring"]
