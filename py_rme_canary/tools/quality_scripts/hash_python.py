#!/usr/bin/env python3
"""Compute a stable hash for quality-pipeline cache keys."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
from pathlib import Path

SKIP_DIRS = {
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
    ".ruff_cache",
    "node_modules",
}

EXTRA_FILES = (
    "pyproject.toml",
    ".pre-commit-config.yaml",
    "quality.sh",
    "py_rme_canary/quality-pipeline/quality_lf.sh",
)

TRACKED_FILENAMES = {"pyproject.toml", "pytest.ini", "setup.py"}


def should_skip(path: Path) -> bool:
    """Return True when a path must be excluded from hashing."""
    return any(part in SKIP_DIRS for part in path.parts)


def normalize_roots(raw_roots: list[str]) -> list[Path]:
    roots: list[Path] = []
    for raw in raw_roots:
        for chunk in raw.split(","):
            candidate = chunk.strip()
            if candidate:
                roots.append(Path(candidate))
    return roots


def _matches_tracked_files(path: Path) -> bool:
    if path.suffix == ".py":
        return True
    return path.name in TRACKED_FILENAMES


def _is_inside_roots(path: Path, roots: list[Path]) -> bool:
    for root in roots:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def _collect_using_git(roots: list[Path]) -> list[Path]:
    cwd = Path.cwd()
    roots_abs = [(cwd / root).resolve() for root in roots]

    try:
        check = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return []

    if check.returncode != 0:
        return []

    cmd = ["git", "ls-files", "-co", "--exclude-standard", "-z"]
    completed = subprocess.run(cmd, check=False, capture_output=True)
    if completed.returncode != 0:
        return []

    files: set[Path] = set()
    for raw in completed.stdout.split(b"\x00"):
        if not raw:
            continue
        rel = raw.decode("utf-8", errors="ignore")
        candidate = (cwd / rel).resolve()
        if should_skip(candidate):
            continue
        if not _matches_tracked_files(candidate):
            continue
        if not _is_inside_roots(candidate, roots_abs):
            continue
        if candidate.exists() and candidate.is_file():
            files.add(candidate)
    return sorted(files)


def _collect_with_walk(roots: list[Path]) -> list[Path]:
    files: set[Path] = set()
    for root in roots:
        target = root.resolve()
        if not target.exists():
            continue

        if target.is_file():
            if _matches_tracked_files(target) and not should_skip(target):
                files.add(target)
            continue

        for dirpath, dirnames, filenames in os.walk(target):
            current = Path(dirpath)
            dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
            if should_skip(current):
                continue
            for filename in filenames:
                candidate = current / filename
                if should_skip(candidate):
                    continue
                if _matches_tracked_files(candidate):
                    files.add(candidate)
    return sorted(files)


def collect_files(roots: list[Path]) -> list[Path]:
    files = _collect_using_git(roots)
    if not files:
        files = _collect_with_walk(roots)

    for extra in EXTRA_FILES:
        extra_path = Path(extra).resolve()
        if extra_path.exists() and extra_path.is_file() and not should_skip(extra_path):
            files.append(extra_path)

    deduped = sorted(set(files))
    return deduped


def build_hash(paths: list[Path], *, mode: str) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path).encode("utf-8", errors="ignore"))
        try:
            if mode == "metadata":
                stat = path.stat()
                digest.update(str(stat.st_size).encode("ascii", errors="ignore"))
                digest.update(str(stat.st_mtime_ns).encode("ascii", errors="ignore"))
            else:
                digest.update(path.read_bytes())
        except OSError:
            continue
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Hash Python sources for quality cache.")
    parser.add_argument("roots", nargs="*", help="Directories/files to include (comma-separated supported).")
    parser.add_argument(
        "--mode",
        choices=("metadata", "content"),
        default="metadata",
        help="metadata (faster) or content (strict) hashing mode.",
    )
    args = parser.parse_args()

    roots = normalize_roots(args.roots or ["py_rme_canary"])
    files = collect_files(roots)
    print(build_hash(files, mode=str(args.mode)))


if __name__ == "__main__":
    main()
