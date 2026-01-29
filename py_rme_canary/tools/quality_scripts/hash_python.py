#!/usr/bin/env python3
"""Compute hash of tracked Python files for caching."""

from __future__ import annotations

import hashlib
from pathlib import Path


SKIP_DIRS = {".venv", "__pycache__", "site-packages", ".tox", "build", "dist"}


def should_skip(path: Path) -> bool:
    """Determine if a file should be ignored."""
    return any(part in SKIP_DIRS for part in path.parts)


def collect_python_files(root: Path = Path(".")) -> list[Path]:
    """Collect Python files excluding skip directories."""
    return sorted(
        [
            path
            for path in root.rglob("*.py")
            if not should_skip(path)
        ]
    )


def main() -> None:
    hash_obj = hashlib.sha256()
    for path in collect_python_files():
        hash_obj.update(path.read_bytes())
    print(hash_obj.hexdigest())


if __name__ == "__main__":
    main()
