#!/usr/bin/env python3
"""
Google AntiGravity Integration Worker
API Docs: https://antigravity.google/docs/get-started
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Literal

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

AnalysisMode = Literal["refactor", "review", "security"]


class AntiGravityClient:
    """Google AntiGravity API wrapper for AI code analysis"""

    BASE_URL = "https://api.antigravity.google/v1"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("ANTIGRAVITY_API_KEY")
        if not self.api_key:
            raise ValueError("ANTIGRAVITY_API_KEY not set")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Quality-Pipeline/2.1.0",
            }
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def analyze_code(self, source: str, file_path: str, mode: AnalysisMode = "refactor") -> dict[str, Any]:
        """Analyze code using AntiGravity AI"""

        endpoint = f"{self.BASE_URL}/analyze"

        payload = {
            "code": source,
            "file_path": file_path,
            "mode": mode,
            "language": "python",
            "options": {"include_fixes": True, "complexity_threshold": 10, "target_python_version": "3.12"},
        }

        try:
            response = self.session.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Parse AntiGravity response format
            # Ref: https://antigravity.google/docs/api-reference#analyze-response
            return {
                "file": file_path,
                "findings": data.get("findings", []),
                "complexity_score": data.get("metrics", {}).get("complexity", 0),
                "suggestions": data.get("suggestions", []),
                "priority": self._calculate_priority(data),
            }

        except requests.HTTPError as e:
            log.error(f"API error for {file_path}: {e.response.status_code}")
            if e.response.status_code == 401:
                log.error("Authentication failed - check ANTIGRAVITY_API_KEY")
            return {"file": file_path, "error": str(e), "findings": []}

        except Exception as e:
            log.error(f"Unexpected error for {file_path}: {e}")
            return {"file": file_path, "error": str(e), "findings": []}

    def _calculate_priority(self, data: dict) -> str:
        """Calculate priority level from AntiGravity response"""

        findings = data.get("findings", [])

        # Count critical/high severity findings
        critical = sum(1 for f in findings if f.get("severity") == "critical")
        high = sum(1 for f in findings if f.get("severity") == "high")

        if critical > 0:
            return "critical"
        elif high > 2:
            return "high"
        elif high > 0 or len(findings) > 5:
            return "medium"
        else:
            return "low"

    def analyze_project(self, project_dir: Path, mode: AnalysisMode = "refactor", max_files: int = 100) -> list[dict]:
        """Analyze entire project"""

        log.info(f"Scanning {project_dir} in mode: {mode}")

        # Find Python files
        py_files = []
        for path in project_dir.rglob("*.py"):
            if any(p in str(path) for p in [".venv", "__pycache__", "site-packages"]):
                continue
            py_files.append(path)

        if len(py_files) > max_files:
            log.warning(f"Found {len(py_files)} files, limiting to {max_files}")
            py_files = py_files[:max_files]

        results = []
        for i, file_path in enumerate(py_files, 1):
            log.info(f"Progress: {i}/{len(py_files)} - {file_path.name}")

            try:
                source = file_path.read_text(encoding="utf-8")
            except Exception as e:
                log.error(f"Failed to read {file_path}: {e}")
                continue

            result = self.analyze_code(source, str(file_path), mode)

            # Only include files with findings
            if result.get("findings") or result.get("suggestions"):
                results.append(result)

        return results

    def batch_analyze(self, files: list[Path], mode: AnalysisMode = "refactor") -> dict[str, Any]:
        """Batch analysis using AntiGravity's batch API (if available)"""

        # TODO: Implement batch endpoint when available
        # For now, fallback to sequential
        log.warning("Batch API not yet implemented, using sequential mode")

        results = []
        for file_path in files:
            try:
                source = file_path.read_text()
                result = self.analyze_code(source, str(file_path), mode)
                results.append(result)
            except Exception as e:
                log.error(f"Failed to analyze {file_path}: {e}")

        return {"results": results, "total": len(results)}


def main():
    parser = argparse.ArgumentParser(description="Google AntiGravity Code Analysis Worker")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--mode", choices=["refactor", "review", "security"], default="refactor")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api-key", help="AntiGravity API key (or use ANTIGRAVITY_API_KEY env)")
    parser.add_argument("--max-files", type=int, default=100)

    args = parser.parse_args()

    try:
        client = AntiGravityClient(api_key=args.api_key)

        results = client.analyze_project(args.project, mode=args.mode, max_files=args.max_files)

        # Save results
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, indent=2))

        # Summary
        high_priority = [r for r in results if r.get("priority") in ["critical", "high"]]
        log.info(f"Analysis complete: {len(results)} files with findings")
        log.info(f"High-priority issues: {len(high_priority)}")

        sys.exit(0)

    except Exception as e:
        log.error(f"Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
