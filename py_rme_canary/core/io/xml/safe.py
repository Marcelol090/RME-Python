from __future__ import annotations

import sys
from typing import Any
from xml.etree import ElementTree as stdlib_etree

# Provide typed aliases from stdlib for use in annotations.
Element = stdlib_etree.Element
ElementTree = stdlib_etree.ElementTree
ParseError = stdlib_etree.ParseError
SubElement = stdlib_etree.SubElement

try:
    import defusedxml.ElementTree as safe_backend
    _HAS_DEFUSEDXML = True
except ImportError:
    safe_backend = stdlib_etree # type: ignore
    _HAS_DEFUSEDXML = False

# Backend functions
_parse = safe_backend.parse
_fromstring = safe_backend.fromstring

if hasattr(safe_backend, "tostring"):
    _tostring = safe_backend.tostring
else:
    _tostring = stdlib_etree.tostring

if hasattr(stdlib_etree, "indent"):
    _indent = stdlib_etree.indent
else:
    def _indent(*args: Any, **kwargs: Any) -> None:
        pass

class SafeETreeModule:
    """Proxy class to look like xml.etree.ElementTree module but using safe functions."""
    Element = Element
    ElementTree = ElementTree
    ParseError = ParseError

    # SubElement is a function in stdlib, so we must wrap it as staticmethod
    # to prevent it from becoming a bound method on this instance.
    SubElement = staticmethod(SubElement)

    @staticmethod
    def parse(*args: Any, **kwargs: Any) -> Any:
        return _parse(*args, **kwargs)

    @staticmethod
    def fromstring(*args: Any, **kwargs: Any) -> Any:
        return _fromstring(*args, **kwargs)

    @staticmethod
    def tostring(*args: Any, **kwargs: Any) -> Any:
        return _tostring(*args, **kwargs)

    @staticmethod
    def indent(*args: Any, **kwargs: Any) -> None:
        return _indent(*args, **kwargs)

# Instance that acts like the module
safe_etree = SafeETreeModule()

# Direct exports for "from safe import parse" style
parse = _parse
fromstring = _fromstring
tostring = _tostring
indent = _indent

__all__ = ["Element", "ElementTree", "ParseError", "SubElement", "parse", "fromstring", "tostring", "indent", "safe_etree"]
