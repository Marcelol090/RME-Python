from __future__ import annotations

import struct
from pathlib import Path

# Common legacy client signatures (DatSignature).
# Maps signature (uint32) -> Client Version (int).
# These are just examples; a full list would come from a database like clients.xml.
KNOWN_DAT_SIGNATURES: dict[int, int] = {
    0x43985288: 740,
    0x439D5A33: 760,
    0x44243C99: 772,
    0x44665426: 780,
    0x4529FA16: 792,
    0x46423082: 800,
    0x46784505: 810,
    0x48566418: 820,
    0x48DD6920: 831,
    0x493E723D: 840,
    0x4A1EA5C4: 850,
    0x4A81881B: 854,
    0x4B28854C: 860,
    0x4C08D696: 861,
    0x4C21FE90: 862,
    0x4D0C5467: 870,
}

def detect_legacy_version(dat_path: str | Path) -> int | None:
    """Read the 4-byte signature from a .dat file and infer the client version."""
    p = Path(dat_path)
    if not p.exists():
        return None

    try:
        with p.open("rb") as f:
            data = f.read(4)
            if len(data) < 4:
                return None
            sig = struct.unpack("<I", data)[0]
            return KNOWN_DAT_SIGNATURES.get(sig)
    except Exception:
        return None

def detect_assets_in_path(path: str | Path) -> tuple[str, int] | None:
    """
    Scans a directory for known asset files and infers the engine and version.
    Returns (engine_type, client_version).

    Engine types: 'tfs' (Legacy), 'canary' (Modern).
    Version: 0 if unknown.
    """
    p = Path(path)
    if p.is_file():
        p = p.parent

    # 1. Check for Modern / Canary assets (JSON catalog)
    # Check current dir and commonly 'assets' subdir
    candidates_modern = [
        p / "catalog-content.json",
        p / "assets" / "catalog-content.json",
        p / "data" / "assets" / "catalog-content.json",
    ]
    for cand in candidates_modern:
        if cand.exists():
            # Canary is typically >= 1300. We don't have a precise version
            # inside catalog-content.json easily without parsing huge files,
            # so we default to a safe modern baseline.
            return ("canary", 1300)

    # 2. Check for Legacy assets (.dat / .spr)
    candidates_legacy = [
        ("Tibia.dat", "Tibia.spr"),
        ("items.dat", "items.spr"),
        ("client.dat", "client.spr"),
    ]

    found_dat: Path | None = None

    for dat_name, spr_name in candidates_legacy:
        d = p / dat_name
        s = p / spr_name
        if d.exists() and s.exists():
            found_dat = d
            break

    if found_dat:
        ver = detect_legacy_version(found_dat)
        return ("tfs", ver if ver is not None else 0)

    return None
