#!/usr/bin/env python3
"""
compare_with_baseline.py
- Compares reports/issues_normalized.json with reports/baseline.json
- Writes new issues to reports/new_issues.json
- Returns exit code 1 if new issues found
"""

from __future__ import annotations

import json
from pathlib import Path

NORMAL = Path("reports/issues_normalized.json")
BASE = Path("reports/baseline.json")
OUT = Path("reports/new_issues.json")


def key_for_issue(i):
    # produce a stable key for dedup/compare
    return "::".join(str(i.get(k, "")) for k in ("tool", "rule", "file", "line", "message"))


def main():
    if not NORMAL.exists():
        print("Normalized issues not found; run normalize step first.")
        raise SystemExit(2)
    current = json.loads(NORMAL.read_text(encoding="utf-8"))
    baseline = json.loads(BASE.read_text(encoding="utf-8")) if BASE.exists() else []

    base_keys = {key_for_issue(i) for i in baseline}
    new = [i for i in current if key_for_issue(i) not in base_keys]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(new, indent=2), encoding="utf-8")
    print(f"New issues: {len(new)} -> {OUT}")
    return 1 if len(new) > 0 else 0


if __name__ == "__main__":
    exit(main())
