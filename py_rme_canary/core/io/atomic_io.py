# atomic_io.py
from __future__ import annotations

import os
from pathlib import Path


def save_bytes_atomic(path: str, data: bytes) -> None:
    """Write bytes to `path` atomically (best-effort across platforms).

    Strategy:
    - write to `path + .tmp`
    - flush + fsync
    - os.replace(tmp, path)
    """

    dst = Path(path)
    tmp = dst.with_suffix(dst.suffix + ".tmp")
    tmp.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, dst)
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
