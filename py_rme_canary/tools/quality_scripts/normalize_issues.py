#!/usr/bin/env python3
"""Issue normalizer - consolidates issues from multiple tools."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


def safe_load_json(path: Path | str) -> Any:
    """Load JSON with graceful fallback."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def normalize_ruff_issues(ruff_data: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not ruff_data:
        return issues

    for issue in ruff_data:
        issues.append(
            {
                "tool": "ruff",
                "code": issue.get("code"),
                "message": issue.get("message"),
                "file": issue.get("filename"),
                "line": issue.get("location", {}).get("row"),
                "column": issue.get("location", {}).get("column"),
                "severity": "high" if issue.get("code", "").startswith("S") else "medium",
            }
        )
    return issues


def normalize_radon_issues(radon_data: Any) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not radon_data:
        return issues

    radon_entries: list[Any] = []
    if isinstance(radon_data, dict):
        for file_entries in radon_data.values():
            if isinstance(file_entries, list):
                radon_entries.extend(file_entries)
    elif isinstance(radon_data, list):
        radon_entries = radon_data

    for entry in radon_entries:
        if not isinstance(entry, dict):
            continue
        complexity = entry.get("complexity", 0)
        issues.append(
            {
                "tool": "radon",
                "function": entry.get("name"),
                "complexity": complexity,
                "file": entry.get("filename"),
                "line": entry.get("lineno"),
                "severity": "high" if complexity > 10 else "medium",
            }
        )
    return issues


def normalize_astgrep_issues(astgrep_data: Any) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not astgrep_data:
        return issues

    if isinstance(astgrep_data, dict):
        astgrep_iter = [astgrep_data]
    elif isinstance(astgrep_data, list):
        astgrep_iter = astgrep_data
    else:
        astgrep_iter = []

    for file_matches in astgrep_iter:
        if not isinstance(file_matches, dict):
            continue
        for match in file_matches.get("matches", []):
            issues.append(
                {
                    "tool": "ast-grep",
                    "file": file_matches.get("file"),
                    "line": match.get("range", {}).get("start", {}).get("line"),
                    "pattern": match.get("text"),
                    "rule": match.get("rule_id"),
                    "severity": "medium",
                }
            )
    return issues


def normalize_all_issues() -> dict[str, Any]:
    all_issues: list[dict[str, Any]] = []

    all_issues.extend(normalize_ruff_issues(safe_load_json(".ruff.json")))
    all_issues.extend(normalize_radon_issues(safe_load_json(".radon.json")))
    all_issues.extend(normalize_astgrep_issues(safe_load_json(".quality_reports/astgrep_results.json")))

    return {
        "issues": all_issues,
        "total": len(all_issues),
        "by_tool": {
            "ruff": len([issue for issue in all_issues if issue["tool"] == "ruff"]),
            "radon": len([issue for issue in all_issues if issue["tool"] == "radon"]),
            "ast-grep": len([issue for issue in all_issues if issue["tool"] == "ast-grep"]),
        },
        "by_severity": {
            "high": len([issue for issue in all_issues if issue["severity"] == "high"]),
            "medium": len([issue for issue in all_issues if issue["severity"] == "medium"]),
        },
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: normalize_issues.py <output_file.json>", file=sys.stderr)
        return 1

    output_path = Path(sys.argv[1])

    print("Normalizando issues...")
    result = normalize_all_issues()

    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"V {result['total']} issues normalizados")
    print(f"  - Ruff: {result['by_tool']['ruff']}")
    print(f"  - Radon: {result['by_tool']['radon']}")
    print(f"  - ast-grep: {result['by_tool']['ast-grep']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
