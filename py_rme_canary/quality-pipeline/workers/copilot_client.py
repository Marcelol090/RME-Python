#!/usr/bin/env python3
"""
GitHub Copilot Integration Worker
Analyzes codebase and generates refactoring suggestions
"""

import argparse
import ast
import json
import logging
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


class ASTRewriter:
    """Helper to perform safe AST-based code rewriting"""

    @staticmethod
    def rewrite(source_code: str, suggestions: list[dict[str, Any]]) -> str:
        """
        Apply suggestions to source code using AST for location and text replacement.
        Preserves comments outside the replaced nodes.
        """
        if not suggestions:
            return source_code

        # Sort suggestions by line descending to avoid offset invalidation
        # assuming non-overlapping changes
        sorted_suggestions = sorted(
            suggestions, key=lambda s: s.get("line", 0), reverse=True
        )

        source_bytes = source_code.encode("utf-8")
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            log.error(f"Failed to parse source code: {e}")
            return source_code

        current_bytes = source_bytes

        for suggestion in sorted_suggestions:
            line = suggestion.get("line", 0)
            fix = suggestion.get("fix")
            if not line or not fix:
                continue

            try:
                # Parse fix to verify syntax and check node type
                # Dedent fix first as it might come with indentation
                dedented_fix = textwrap.dedent(fix)
                # Verify fix syntax
                ast.parse(dedented_fix)

                # Find target node
                target_node = ASTRewriter._find_node_at_line(tree, line)
                if not target_node:
                    log.warning(f"Could not find AST node at line {line}")
                    continue

                # Calculate byte offsets
                start_byte = ASTRewriter._get_byte_offset(
                    source_bytes, target_node.lineno, target_node.col_offset
                )

                if not hasattr(target_node, "end_lineno") or not hasattr(
                    target_node, "end_col_offset"
                ):
                    log.warning(f"AST node at line {line} missing end position")
                    continue

                end_byte = ASTRewriter._get_byte_offset(
                    source_bytes, target_node.end_lineno, target_node.end_col_offset
                )

                # Indentation handling
                indent_col = target_node.col_offset

                # Apply indentation to all lines except the first one
                # because the first line is appended to existing indentation (current_bytes[:start_byte])
                fix_lines = dedented_fix.splitlines(keepends=True)
                if not fix_lines:
                    continue

                indent_str = " " * indent_col
                indented_lines = [fix_lines[0]] + [
                    indent_str + line for line in fix_lines[1:]
                ]
                indented_fix = "".join(indented_lines)

                # Apply replacement
                current_bytes = (
                    current_bytes[:start_byte]
                    + indented_fix.encode("utf-8")
                    + current_bytes[end_byte:]
                )

            except Exception as e:
                log.error(f"Failed to apply fix at line {line}: {e}")
                continue

        return current_bytes.decode("utf-8")

    @staticmethod
    def _find_node_at_line(tree: ast.AST, line: int) -> ast.AST | None:
        """Find the smallest statement/expression node starting at line"""
        candidates = []
        for node in ast.walk(tree):
            if hasattr(node, "lineno") and node.lineno == line:
                candidates.append(node)

        if not candidates:
            return None

        # Return the first one (parent usually, which is the statement)
        return candidates[0]

    @staticmethod
    def _get_byte_offset(source_bytes: bytes, line: int, col: int) -> int:
        """Convert 1-based line and 0-based col to byte offset"""
        current_line = 1
        byte_pos = 0
        while current_line < line:
            try:
                # Find next newline
                next_newline = source_bytes.index(b"\n", byte_pos) + 1
                byte_pos = next_newline
                current_line += 1
            except ValueError:
                return len(source_bytes)

        return min(byte_pos + col, len(source_bytes))


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

    def apply_suggestions(
        self, suggestions_file: Path, confidence_threshold: float = 0.9
    ) -> int:
        """Apply high-confidence suggestions automatically"""

        log.info(f"Loading suggestions from {suggestions_file}")

        try:
            data = json.loads(suggestions_file.read_text())
        except Exception as e:
            log.error(f"Failed to load suggestions: {e}")
            return 0

        # Group suggestions by file
        files_suggestions: dict[str, list[dict]] = {}
        for item in data:
            if item.get("confidence", 0) < confidence_threshold:
                continue

            file_path_str = item["file"]
            if file_path_str not in files_suggestions:
                files_suggestions[file_path_str] = []
            files_suggestions[file_path_str].append(item.get("suggestions", []))

        # Flatten suggestions list structure if needed?
        # The prompt in analyze_file returns:
        # { "suggestions": [ ... ], ... }
        # And apply_suggestions reads a list of these results?
        # "Return JSON format: { ... }" for single file.
        # analyze_project returns a list of these dicts.
        # So `data` is a list of dicts, each has "file" and "suggestions" (list).

        applied = 0

        # We need to restructure slightly because the previous loop was iterating 'data'
        # but 'data' items contain a list of 'suggestions'.
        # The existing code: `for item in data:` checks `item.get("confidence")`.
        # The `analyze_file` output has top-level `confidence` and `suggestions` list.
        # Wait, the prompt says:
        # {
        #   "suggestions": [ { ... } ],
        #   "complexity_score": ...,
        #   "confidence": ...
        # }
        # So the confidence is per file analysis?
        # Yes.

        for item in data:
            if item.get("confidence", 0) < confidence_threshold:
                continue

            file_path = Path(item["file"])
            if not file_path.exists():
                log.warning(f"File not found: {file_path}")
                continue

            suggestions = item.get("suggestions", [])
            if not suggestions:
                continue

            log.info(f"Applying {len(suggestions)} fix(es) to {file_path}")

            try:
                source = file_path.read_text(encoding="utf-8")
                new_source = ASTRewriter.rewrite(source, suggestions)

                if new_source != source:
                    file_path.write_text(new_source, encoding="utf-8")
                    applied += len(suggestions)

                    # Run formatter
                    try:
                        subprocess.run(
                            ["ruff", "format", str(file_path)],
                            check=True,
                            capture_output=True
                        )
                    except subprocess.CalledProcessError as e:
                        log.warning(f"Failed to format {file_path}: {e}")
                    except FileNotFoundError:
                        log.warning("ruff not found, skipping formatting")

            except Exception as e:
                log.error(f"Failed to apply fixes to {file_path}: {e}")

        log.info(f"Applied fixes to {applied} suggestion items")
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
