from __future__ import annotations

import platform
import struct


def _python_bits() -> int:
    # Pointer-size is the most reliable indicator for the Python process.
    return int(struct.calcsize("P") * 8)


def _os_bits_best_effort() -> int | None:
    # platform.architecture() reports *python* architecture on many platforms.
    # Prefer an environment/processor hint when available.
    try:
        machine = platform.machine().lower()
    except Exception:
        machine = ""
    if machine in {"amd64", "x86_64", "arm64", "aarch64"}:
        return 64
    if machine in {"i386", "i686", "x86"}:
        return 32
    return None


def assert_64bit_runtime() -> None:
    """Fail-fast if running under a 32-bit Python runtime.

    Requirement: runtime must be 64-bit to avoid address-space exhaustion
    and memory fragmentation under large maps/assets.
    """

    py_bits = _python_bits()
    if py_bits >= 64:
        return

    os_bits = _os_bits_best_effort()
    os_msg = "unknown"
    if os_bits == 32:
        os_msg = "32-bit"
    elif os_bits == 64:
        os_msg = "64-bit"

    raise RuntimeError(
        "64-bit runtime required. "
        f"Detected Python={py_bits}-bit on OS={os_msg}. "
        "Install a 64-bit Python and recreate the venv. "
        "If your OS is 32-bit, you must use a 64-bit OS to run this build."
    )
