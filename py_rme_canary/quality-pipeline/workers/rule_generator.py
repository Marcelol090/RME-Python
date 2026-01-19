#!/usr/bin/env python3
"""
LLM-Powered ast-grep Rule Generator
Provider-agnostic: Copilot, AntiGravity, Claude API
"""

import argparse
import ast
import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import requests
import yaml
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


class CodebaseAnalyzer:
    """Analyze Python codebase for anti-patterns"""

    def analyze_project(self, project_dir: Path) -> dict[str, Any]:
        """Walk AST and detect common anti-patterns"""

        log.info(f"Analyzing {project_dir} for anti-patterns")

        patterns = {
            "bare_except": [],
            "mutable_defaults": [],
            "type_comparisons": [],
            "none_comparisons": [],
            "global_usage": [],
            "print_statements": [],
        }

        py_files = [p for p in project_dir.rglob("*.py") if not any(x in str(p) for x in [".venv", "__pycache__"])]

        for file_path in py_files:
            try:
                source = file_path.read_text()
                tree = ast.parse(source, filename=str(file_path))
                self._walk_ast(tree, file_path, patterns)
            except SyntaxError:
                log.warning(f"Syntax error in {file_path}, skipping")
                continue

        return {
            "project": str(project_dir),
            "files_analyzed": len(py_files),
            "patterns": patterns,
            "summary": {k: len(v) for k, v in patterns.items()},
        }

    def _walk_ast(self, tree: ast.AST, file_path: Path, patterns: dict):
        """Walk AST and collect anti-pattern instances"""

        for node in ast.walk(tree):
            # Bare except
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                patterns["bare_except"].append({"file": str(file_path), "line": node.lineno})

            # Mutable default arguments
            if isinstance(node, ast.FunctionDef):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        patterns["mutable_defaults"].append(
                            {"file": str(file_path), "line": node.lineno, "function": node.name}
                        )

            # Type comparisons (type(x) == Y)
            if isinstance(node, ast.Compare):
                if (
                    isinstance(node.left, ast.Call)
                    and isinstance(node.left.func, ast.Name)
                    and node.left.func.id == "type"
                ):
                    patterns["type_comparisons"].append({"file": str(file_path), "line": node.lineno})

            # Global keyword
            if isinstance(node, ast.Global):
                patterns["global_usage"].append({"file": str(file_path), "line": node.lineno, "names": node.names})

            # Print statements
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                patterns["print_statements"].append({"file": str(file_path), "line": node.lineno})


class LLMProvider(ABC):
    """Abstract base for LLM providers"""

    @abstractmethod
    def generate_rules(self, analysis: dict[str, Any], max_rules: int = 20) -> str:
        """Generate ast-grep YAML rules from analysis"""
        pass


class CopilotProvider(LLMProvider):
    """GitHub Copilot (OpenAI backend)"""

    def __init__(self):
        api_key = os.getenv("GITHUB_TOKEN")
        if not api_key:
            raise ValueError("GITHUB_TOKEN not set")
        self.client = OpenAI(api_key=api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def generate_rules(self, analysis: dict[str, Any], max_rules: int = 20) -> str:
        """Generate rules via Copilot"""

        summary = analysis["summary"]
        patterns = analysis["patterns"]

        prompt = f"""Generate ast-grep rules (YAML format) to detect and fix these Python anti-patterns:

Detected patterns:
- Bare except clauses: {summary["bare_except"]}
- Mutable default args: {summary["mutable_defaults"]}
- Type comparisons: {summary["type_comparisons"]}
- Global keyword usage: {summary["global_usage"]}
- Print statements: {summary["print_statements"]}

Generate up to {max_rules} rules in this exact format:

```yaml
rules:
  - id: rule-name
    message: "Description"
    severity: warning
    language: python
    rule:
      pattern: $PATTERN
    fix: |
      $FIX
```

Focus on high-impact patterns. Return ONLY valid YAML, no explanations."""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at creating ast-grep rules for Python."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=3000,
        )

        content = response.choices[0].message.content

        # Extract YAML from markdown if present
        if "```yaml" in content:
            content = content.split("```yaml")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return content.strip()


class AntiGravityProvider(LLMProvider):
    """Google AntiGravity API"""

    BASE_URL = "https://api.antigravity.google/v1"

    def __init__(self):
        self.api_key = os.getenv("ANTIGRAVITY_API_KEY")
        if not self.api_key:
            raise ValueError("ANTIGRAVITY_API_KEY not set")

        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def generate_rules(self, analysis: dict[str, Any], max_rules: int = 20) -> str:
        """Generate rules via AntiGravity"""

        endpoint = f"{self.BASE_URL}/generate"

        payload = {
            "task": "ast-grep-rules",
            "language": "python",
            "analysis": analysis["summary"],
            "max_rules": max_rules,
            "format": "yaml",
        }

        response = self.session.post(endpoint, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        return data.get("rules_yaml", "")


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API"""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.base_url = "https://api.anthropic.com/v1/messages"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def generate_rules(self, analysis: dict[str, Any], max_rules: int = 20) -> str:
        """Generate rules via Claude"""

        summary = analysis["summary"]

        prompt = f"""Generate ast-grep YAML rules for these Python anti-patterns:

{json.dumps(summary, indent=2)}

Output {max_rules} rules in valid YAML format. Include pattern matching and fixes."""

        headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}],
        }

        response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        content = data["content"][0]["text"]

        # Extract YAML
        if "```yaml" in content:
            content = content.split("```yaml")[1].split("```")[0]

        return content.strip()


class RuleGenerator:
    """Main rule generation orchestrator"""

    PROVIDERS = {"copilot": CopilotProvider, "antigravity": AntiGravityProvider, "claude": ClaudeProvider}

    def __init__(self, provider: str):
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}")

        self.provider = self.PROVIDERS[provider]()
        log.info(f"Initialized provider: {provider}")

    def generate(self, analysis: dict[str, Any], output: Path, max_rules: int = 20) -> bool:
        """Generate and validate ast-grep rules"""

        log.info(f"Generating up to {max_rules} rules")

        # Generate via LLM
        yaml_content = self.provider.generate_rules(analysis, max_rules)

        # Validate YAML
        try:
            rules = yaml.safe_load(yaml_content)

            if not isinstance(rules, dict) or "rules" not in rules:
                log.error("Invalid YAML structure: missing 'rules' key")
                return False

            rule_count = len(rules["rules"])
            log.info(f"Generated {rule_count} valid rule(s)")

        except yaml.YAMLError as e:
            log.error(f"Invalid YAML generated: {e}")
            return False

        # Save
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(yaml_content)

        log.info(f"Saved rules to {output}")
        return True


def main():
    parser = argparse.ArgumentParser(description="LLM-Powered ast-grep Rule Generator")
    parser.add_argument("--analyze", type=Path, help="Analyze project directory")
    parser.add_argument("--provider", choices=["copilot", "antigravity", "claude"])
    parser.add_argument("--analysis", type=Path, help="Use existing analysis JSON")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-rules", type=int, default=20)

    args = parser.parse_args()

    try:
        # Analyze or load
        if args.analyze:
            analyzer = CodebaseAnalyzer()
            analysis = analyzer.analyze_project(args.analyze)

            # Save analysis
            args.output.write_text(json.dumps(analysis, indent=2))
            log.info(f"Analysis saved to {args.output}")
            sys.exit(0)

        elif args.analysis and args.provider:
            # Generate rules
            analysis = json.loads(args.analysis.read_text())

            generator = RuleGenerator(args.provider)

            if generator.generate(analysis, args.output, args.max_rules):
                sys.exit(0)
            else:
                sys.exit(1)

        else:
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        log.error(f"Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
