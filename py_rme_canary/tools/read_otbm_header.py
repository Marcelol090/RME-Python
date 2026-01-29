from __future__ import annotations

import argparse

from py_rme_canary.core.io.otbm_loader import load_game_map
from py_rme_canary.core.runtime import assert_64bit_runtime


def main() -> int:
    # Do not rely on 64-bit for safety; still enforce it to guarantee address space.
    assert_64bit_runtime()

    parser = argparse.ArgumentParser(description="Reads OTBM header (minimal parse).")
    parser.add_argument("path", help="Path to .otbm file")
    parser.add_argument(
        "--allow-unsupported",
        action="store_true",
        help="Do not fail for OTBM versions above known maximum",
    )
    parser.add_argument(
        "--count-items",
        action="store_true",
        help="Load and count items (includes ground items)",
    )
    args = parser.parse_args()

    m = load_game_map(args.path, allow_unsupported_versions=args.allow_unsupported)
    h = m.header

    print("OTBM header")
    print(f"  otbm_version: {h.otbm_version}")
    print(f"  width: {h.width}")
    print(f"  height: {h.height}")

    if args.count_items:
        count = 0
        for t in m.tiles.values():
            if t.ground is not None:
                count += 1
            count += len(t.items)
        print(f"  items_total: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
