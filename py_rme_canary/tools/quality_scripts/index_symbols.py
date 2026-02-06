#!/usr/bin/env python3
"""Symbol indexer - extracts functions/classes across the project."""

from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path
from typing import Any


SKIP_DIRS: set[str] = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "site-packages",
    ".tox",
    "build",
    "dist",
    ".quality_cache",
    ".quality_reports",
    ".quality_tmp",
    ".mypy_cache",
    ".pytest_cache",
}


def should_skip(path: Path) -> bool:
    """Return True if file should be ignored."""
    return any(part in SKIP_DIRS for part in path.parts)


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


def index_all_symbols(roots: list[Path]) -> dict[str, Any]:
    """Index all symbols under roots."""
    all_symbols: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    total_files = 0

    for root in roots:
        target = root.resolve()
        if not target.exists():
            continue

        if target.is_file():
            if target.suffix == ".py" and not should_skip(target):
                total_files += 1
                symbols = extract_symbols(target)
                for symbol in symbols:
                    if "error" in symbol:
                        errors.append(symbol)  # type: ignore[arg-type]
                    else:
                        all_symbols.append(symbol)
            continue

        for dirpath, dirnames, filenames in os.walk(target):
            current = Path(dirpath)
            dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
            if should_skip(current):
                continue
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                path = current / filename
                if should_skip(path):
                    continue
                total_files += 1
                symbols = extract_symbols(path)
                for symbol in symbols:
                    if "error" in symbol:
                        errors.append(symbol)  # type: ignore[arg-type]
                    else:
                        all_symbols.append(symbol)

    return {
        "symbols": all_symbols,
        "errors": errors,
        "total_files": total_files,
    }


def main() -> int:
    """Entry point."""
    if len(sys.argv) < 2:
        print("Usage: index_symbols.py <output_file.json> [root ...]", file=sys.stderr)
        return 1

    output_path = Path(sys.argv[1])
    roots = [Path(p) for p in sys.argv[2:] if str(p).strip()]
    if not roots:
        roots = [Path(".")]

    print("Indexando simbolos...")
    result = index_all_symbols(roots)

    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"V {len(result['symbols'])} simbolos indexados")
    if result["errors"]:
        print(f"? {len(result['errors'])} arquivo(s) com erro", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
