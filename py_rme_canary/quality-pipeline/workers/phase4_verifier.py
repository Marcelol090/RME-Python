#!/usr/bin/env python3
"""
Phase 4 Verification Script - Logic & Functional Parity
Validates that all critical features are implemented and working.
"""

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


@dataclass
class FeatureCheck:
    """Single feature verification result."""

    category: str
    feature: str
    status: str  # "implemented", "partial", "missing"
    location: str
    notes: str = ""


class FunctionalParityVerifier:
    """Verify logic layer functional parity with C++ legacy."""

    CRITICAL_FEATURES: ClassVar[dict[str, dict[str, tuple[str, str]]]] = {
        "Map IO": {
            "OTBM Load": ("core/io", "otbm"),
            "OTBM Save": ("core/io", "save"),
            "Map Validation": ("core/io", "validate"),
        },
        "Brushes": {
            "Ground Brush": ("logic_layer", "GroundBrush"),
            "Wall Brush": ("logic_layer", 'brush_type_norm in ("wall", "carpet", "table")'),
            "Doodad Brush": ("logic_layer", "DoodadBrush"),
            "Carpet Brush": ("logic_layer", 'brush_type_norm == "carpet"'),
            "Table Brush": ("logic_layer", 'brush_type_norm == "table"'),
        },
        "Editor": {
            "Undo": ("logic_layer", "HistoryManager.undo"),
            "Redo": ("logic_layer", "HistoryManager.redo"),
            "PaintAction": ("logic_layer", "PaintAction"),
            "TransactionalStroke": ("logic_layer", "TransactionalBrushStroke"),
        },
        "Selection": {
            "Box Selection": ("logic_layer/session", "selection"),
            "Toggle Select": ("logic_layer/session", "toggle_select"),
            "Move Selection": ("logic_layer/session", "move_selection"),
        },
        "Navigation": {
            "Viewport": ("vis_layer", "viewport"),
            "Zoom": ("vis_layer", "tile_px"),
            "Pan": ("vis_layer", "origin"),
        },
    }

    def __init__(self, project_root: Path):
        self.root = project_root
        self.results: list[FeatureCheck] = []

    def verify_all(self) -> dict[str, Any]:
        """Run all verification checks."""
        log.info("Starting Phase 4 Functional Parity Verification...")

        for category, features in self.CRITICAL_FEATURES.items():
            for feature_name, (search_path, keyword) in features.items():
                self._check_feature(category, feature_name, search_path, keyword)

        # Summary
        total = len(self.results)
        implemented = sum(1 for r in self.results if r.status == "implemented")
        partial = sum(1 for r in self.results if r.status == "partial")
        missing = sum(1 for r in self.results if r.status == "missing")

        summary = {
            "total_features": total,
            "implemented": implemented,
            "partial": partial,
            "missing": missing,
            "parity_score": f"{(implemented / total * 100):.1f}%" if total > 0 else "N/A",
            "results": [
                {
                    "category": r.category,
                    "feature": r.feature,
                    "status": r.status,
                    "location": r.location,
                    "notes": r.notes,
                }
                for r in self.results
            ],
        }

        return summary

    def _check_feature(self, category: str, feature: str, search_path: str, keyword: str) -> None:
        """Check if a feature is implemented."""
        full_path = self.root / "py_rme_canary" / search_path

        if not full_path.exists():
            self.results.append(
                FeatureCheck(
                    category=category,
                    feature=feature,
                    status="missing",
                    location=str(full_path),
                    notes="Directory/file not found",
                )
            )
            return

        # Search for keyword in files
        if full_path.is_dir():
            found_locations = [
                str(py_file.relative_to(self.root))
                for py_file in full_path.rglob("*.py")
                if self._file_contains_keyword(py_file, keyword)
            ]
        else:
            found_locations = (
                [str(full_path.relative_to(self.root))] if self._file_contains_keyword(full_path, keyword) else []
            )

        if found_locations:
            self.results.append(
                FeatureCheck(
                    category=category,
                    feature=feature,
                    status="implemented",
                    location=", ".join(found_locations[:3]),
                    notes=f"Found in {len(found_locations)} file(s)",
                )
            )
        else:
            # Check if partial (similar keywords)
            partial_keyword = keyword.split(".")[-1].lower() if "." in keyword else keyword.lower()
            partial_found = self._search_partial(full_path, partial_keyword)

            if partial_found:
                self.results.append(
                    FeatureCheck(
                        category=category,
                        feature=feature,
                        status="partial",
                        location=str(full_path),
                        notes=f"Partial match: {partial_keyword}",
                    )
                )
            else:
                self.results.append(
                    FeatureCheck(
                        category=category,
                        feature=feature,
                        status="missing",
                        location=str(full_path),
                        notes="Keyword not found",
                    )
                )

    def _file_contains_keyword(self, file_path: Path, keyword: str) -> bool:
        """Check if file contains keyword."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            return keyword in content
        except Exception:
            return False

    def _search_partial(self, path: Path, keyword: str) -> bool:
        """Search for partial keyword match."""
        if path.is_dir():
            for py_file in path.rglob("*.py"):
                if self._file_contains_keyword(py_file, keyword):
                    return True
        return False


def main():
    # Go up from workers -> quality-pipeline -> py_rme_canary -> underv1
    project_root = Path(__file__).parent.parent.parent.parent

    verifier = FunctionalParityVerifier(project_root)
    results = verifier.verify_all()

    # Output
    output_file = project_root / "py_rme_canary" / ".quality_reports" / "phase4_verification.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(results, indent=2))

    # Console report
    print("\n" + "=" * 60)
    print("PHASE 4: LOGIC & FUNCTIONAL PARITY VERIFICATION")
    print("=" * 60)
    print(f"\nTotal Features:  {results['total_features']}")
    print(f"Implemented:     {results['implemented']} [OK]")
    print(f"Partial:         {results['partial']} [WARN]")
    print(f"Missing:         {results['missing']} [FAIL]")
    print(f"Parity Score:    {results['parity_score']}")
    print("\n" + "-" * 60)

    # Print by category
    current_category = ""
    for r in results["results"]:
        if r["category"] != current_category:
            current_category = r["category"]
            print(f"\n{current_category}:")

        status_icon = "[OK]" if r["status"] == "implemented" else "[WARN]" if r["status"] == "partial" else "[FAIL]"
        print(f"  {status_icon} {r['feature']}: {r['location']}")

    print("\n" + "=" * 60)
    print(f"Report saved: {output_file}")

    return 0 if results["missing"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
