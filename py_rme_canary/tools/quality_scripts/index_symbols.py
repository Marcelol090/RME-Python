#!/usr/bin/env python3
"""Symbol indexer - extracts functions/classes across the project."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import sys
from typing import Any


def should_skip(path: Path) -> bool:
    """Return True if file should be ignored."""
    skip_patterns = (".venv", "__pycache__", "site-packages", ".tox", "build", "dist")
    return any(p in str(path) for p in skip_patterns)


def extract_symbols(path: Path) -> list[dict[str, Any]]:
    """Extract symbol entries from a python file."""
    symbols: list[dict[str, Any]] = []

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        return [{"error": str(exc), "file": str(path)}]

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(
                {
                    "type": node.__class__.__name__,
                    "name": node.name,
                    "file": str(path),
                    "line": node.lineno,
                    "decorators": [
                        dec.id if isinstance(dec, ast.Name) else str(dec)
                        for dec in getattr(node, "decorator_list", [])
                    ],
                }
            )

    return symbols


def index_all_symbols(root: Path = Path(".")) -> dict[str, Any]:
    """Index all symbols under root."""
    all_symbols: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for path in root.rglob("*.py"):
        if should_skip(path):
            continue

        symbols = extract_symbols(path)
        for symbol in symbols:
            if "error" in symbol:
                errors.append(symbol)  # type: ignore[arg-type]
            else:
                all_symbols.append(symbol)

    return {
        "symbols": all_symbols,
        "errors": errors,
        "total_files": len(all_symbols),
    }


def main() -> int:
    """Entry point."""
    if len(sys.argv) < 2:
        print("Usage: index_symbols.py <output_file.json>", file=sys.stderr)
        return 1

    output_path = Path(sys.argv[1])

    print("Indexando simbolos...")
    result = index_all_symbols()

    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"V {len(result['symbols'])} simbolos indexados")
    if result["errors"]:
        print(f"? {len(result['errors'])} arquivo(s) com erro", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
