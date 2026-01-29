#!/usr/bin/env python3
"""
normalize_issues.py
Unify raw reports into reports/issues_normalized.json
Normalizes entries to:
  { tool, rule, file, line, message, severity?, meta? }
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

RAW = Path("reports/raw")
OUT = Path("reports/issues_normalized.json")


def load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def normalize() -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    # Ruff standard report
    ruff_p = RAW / "ruff.json"
    if ruff_p.exists():
        data = load_json(ruff_p) or []
        for it in data:
            issues.append(
                {
                    "tool": "ruff",
                    "rule": it.get("code"),
                    "file": it.get("filename"),
                    "line": it.get("location", {}).get("row"),
                    "message": it.get("message"),
                    "severity": it.get("severity"),
                }
            )

    # Ruff C901 (explicit)
    ruff_c901_p = RAW / "ruff_c901.json"
    if ruff_c901_p.exists():
        data = load_json(ruff_c901_p) or []
        for it in data:
            issues.append(
                {
                    "tool": "ruff_c901",
                    "rule": it.get("code") or "C901",
                    "file": it.get("filename"),
                    "line": it.get("location", {}).get("row"),
                    "message": it.get("message") or "complexity",
                    "severity": it.get("severity"),
                }
            )

    # MyPy (text parse)
    mypy_p = RAW / "mypy.txt"
    if mypy_p.exists():
        pattern = re.compile(r"^(?P<file>.+?):(?P<line>\d+): (?P<level>error|note): (?P<msg>.+?)( \[(?P<code>.+?)\])?$")
        for ln in mypy_p.read_text(encoding="utf-8").splitlines():
            m = pattern.match(ln)
            if m:
                issues.append(
                    {
                        "tool": "mypy",
                        "rule": m.group("code") or "mypy",
                        "file": m.group("file"),
                        "line": int(m.group("line")),
                        "message": m.group("msg").strip(),
                        "severity": "error",
                    }
                )

    # Radon (complexity) - radon cc . -j outputs mapping file -> list of blocks
    radon_p = RAW / "radon.json"
    if radon_p.exists():
        data = load_json(radon_p) or {}
        for fname, blocks in data.items() if isinstance(data, dict) else []:
            for block in blocks:
                complexity = block.get("complexity")
                name = block.get("name")
                lineno = block.get("lineno")
                issues.append(
                    {
                        "tool": "radon",
                        "rule": "C901",
                        "file": fname,
                        "line": lineno,
                        "message": f"cyclomatic complexity {complexity} in {name}",
                        "meta": {"complexity": complexity, "block": name},
                        "severity": "warning",
                    }
                )

    # ast-grep (scan / run)
    ag_p = RAW / "astgrep.json"
    if ag_p.exists():
        ag = load_json(ag_p)
        matches = ag.get("matches") if isinstance(ag, dict) and ag.get("matches") is not None else ag
        for m in matches or []:
            rng = m.get("range", {})
            issues.append(
                {
                    "tool": "ast-grep",
                    "rule": m.get("ruleId") or m.get("rule_id") or m.get("id"),
                    "file": m.get("file") or m.get("path"),
                    "line": (rng.get("start") or {}).get("line"),
                    "message": m.get("message") or m.get("text") or "ast-grep match",
                    "meta": m.get("metaVariables") or m.get("meta") or None,
                    "severity": "info",
                }
            )

    # semgrep
    semgrep_p = RAW / "semgrep.json"
    if semgrep_p.exists():
        sdata = load_json(semgrep_p) or {}
        for r in sdata.get("results", []) if isinstance(sdata, dict) else sdata:
            issues.append(
                {
                    "tool": "semgrep",
                    "rule": r.get("check_id") or r.get("rule_id"),
                    "file": r.get("path"),
                    "line": r.get("start", {}).get("line"),
                    "message": r.get("extra", {}).get("message") or r.get("message"),
                    "meta": r.get("extra", {}).get("meta") if isinstance(r.get("extra"), dict) else None,
                    "severity": "warning",
                }
            )

    # bandit
    bandit_p = RAW / "bandit.json"
    if bandit_p.exists():
        bdata = load_json(bandit_p) or {}
        for r in bdata.get("results", []) if isinstance(bdata, dict) else []:
            issues.append(
                {
                    "tool": "bandit",
                    "rule": r.get("test_id"),
                    "file": r.get("filename"),
                    "line": r.get("line_number"),
                    "message": r.get("issue_text"),
                    "severity": "warning",
                }
            )

    return issues


def main():
    issues = normalize()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(issues, indent=2), encoding="utf-8")
    print(f"Normalized {len(issues)} issues -> {OUT}")


if __name__ == "__main__":
    main()
