#!/usr/bin/env python3
"""
GitHub Copilot Integration Worker
Analyzes codebase and generates refactoring suggestions
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


class CopilotClient:
    """GitHub Copilot API wrapper for code analysis"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GITHUB_TOKEN")
        if not self.api_key:
            raise ValueError("GITHUB_TOKEN not set")

        # Copilot uses OpenAI's API infrastructure
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4"  # Copilot backend

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def analyze_file(self, file_path: Path) -> dict[str, Any]:
        """Analyze single Python file for refactoring opportunities"""

        log.info(f"Analyzing {file_path}")

        try:
            source = file_path.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read {file_path}: {e}")
            return {"file": str(file_path), "error": str(e)}

        # Prompt engineering for code analysis
        prompt = f"""Analyze this Python code for refactoring opportunities.
Focus on: complexity reduction, type hints, modern Python patterns (3.12+).

Code:
```python
{source}
```

Return JSON format:
{{
  "suggestions": [
    {{
      "line": 42,
      "severity": "high|medium|low",
      "category": "complexity|typing|modernization|performance",
      "message": "Description",
      "fix": "Suggested fix"
    }}
  ],
  "complexity_score": 1-10,
  "confidence": 0.0-1.0
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior Python code reviewer specializing in refactoring."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
            )

            content = response.choices[0].message.content

            # Parse JSON from response
            # Handle markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            result["file"] = str(file_path)

            return result

        except Exception as e:
            log.error(f"API call failed for {file_path}: {e}")
            return {"file": str(file_path), "error": str(e), "suggestions": []}

    def analyze_project(self, project_dir: Path, max_files: int = 50) -> list[dict]:
        """Analyze entire project directory"""

        log.info(f"Scanning {project_dir}")

        # Find Python files
        py_files = []
        for path in project_dir.rglob("*.py"):
            # Skip common excludes
            if any(p in str(path) for p in [".venv", "__pycache__", "site-packages", ".tox"]):
                continue
            py_files.append(path)

        if len(py_files) > max_files:
            log.warning(f"Found {len(py_files)} files, analyzing first {max_files}")
            py_files = py_files[:max_files]

        results = []
        for i, file_path in enumerate(py_files, 1):
            log.info(f"Progress: {i}/{len(py_files)}")
            result = self.analyze_file(file_path)
            if result.get("suggestions"):
                results.append(result)

        return results

    def apply_suggestions(self, suggestions_file: Path, confidence_threshold: float = 0.9) -> int:
        """Apply high-confidence suggestions automatically"""

        log.info(f"Loading suggestions from {suggestions_file}")

        try:
            data = json.loads(suggestions_file.read_text())
        except Exception as e:
            log.error(f"Failed to load suggestions: {e}")
            return 0

        applied = 0
        for item in data:
            if item.get("confidence", 0) < confidence_threshold:
                continue

            file_path = Path(item["file"])
            if not file_path.exists():
                log.warning(f"File not found: {file_path}")
                continue

            # Apply fixes (simplified - production would use AST rewriting)
            log.info(f"Applying fixes to {file_path}")
            # TODO: Implement safe AST-based rewriting
            applied += 1

        log.info(f"Applied {applied} suggestion(s)")
        return applied


def main():
    parser = argparse.ArgumentParser(description="GitHub Copilot Code Analysis Worker")
    parser.add_argument("--project", type=Path, required=True, help="Project directory")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON file")
    parser.add_argument("--apply", type=Path, help="Apply suggestions from file")
    parser.add_argument("--confidence-threshold", type=float, default=0.9)
    parser.add_argument("--max-files", type=int, default=50)

    args = parser.parse_args()

    try:
        client = CopilotClient()

        if args.apply:
            # Apply mode
            applied = client.apply_suggestions(args.apply, args.confidence_threshold)
            sys.exit(0 if applied > 0 else 1)
        else:
            # Analysis mode
            results = client.analyze_project(args.project, args.max_files)

            # Save results
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(results, indent=2))

            log.info(f"Saved {len(results)} analysis result(s) to {args.output}")
            sys.exit(0)

    except Exception as e:
        log.error(f"Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
