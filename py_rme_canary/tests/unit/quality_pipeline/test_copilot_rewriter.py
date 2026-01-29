
import importlib.util
import sys
from pathlib import Path
import pytest
import textwrap

# Locate the worker module
# Assuming we run from repo root or the tests folder structure is preserved
# py_rme_canary/tests/unit/quality_pipeline/test_copilot_rewriter.py
# parents[3] is py_rme_canary
# But we need repo root to find py_rme_canary/quality-pipeline...
# Actually we can just find it relative to py_rme_canary
REPO_ROOT = Path(__file__).parents[4]
WORKER_PATH = REPO_ROOT / "py_rme_canary/quality-pipeline/workers/copilot_client.py"

if not WORKER_PATH.exists():
    # Fallback if structure is different
    WORKER_PATH = Path("py_rme_canary/quality-pipeline/workers/copilot_client.py").absolute()

# Import the module dynamically
spec = importlib.util.spec_from_file_location("copilot_client", WORKER_PATH)
copilot_client = importlib.util.module_from_spec(spec)
sys.modules["copilot_client"] = copilot_client
spec.loader.exec_module(copilot_client)

ASTRewriter = copilot_client.ASTRewriter

class TestASTRewriter:
    def test_single_replacement(self):
        source = textwrap.dedent("""
            def foo():
                x = 1
                return x
        """).strip()

        # Line 2: x = 1
        # Fix: x = 2

        suggestions = [
            {
                "line": 2,
                "fix": "x = 2"
            }
        ]

        result = ASTRewriter.rewrite(source, suggestions)
        expected = textwrap.dedent("""
            def foo():
                x = 2
                return x
        """).strip()

        assert result == expected

    def test_indentation_handling(self):
        source = textwrap.dedent("""
            def foo():
                if True:
                    x = 1
        """).strip()

        # Line 3: x = 1. Indented 8 spaces.
        # Fix: y = 2

        suggestions = [
            {
                "line": 3,
                "fix": "y = 2"
            }
        ]

        result = ASTRewriter.rewrite(source, suggestions)
        expected = textwrap.dedent("""
            def foo():
                if True:
                    y = 2
        """).strip()

        assert result == expected

    def test_multi_line_fix(self):
        source = textwrap.dedent("""
            def foo():
                x = [1, 2]
        """).strip()

        # Line 2: x = [1, 2]
        # Fix: multi-line list

        fix = textwrap.dedent("""
            x = [
                1,
                2
            ]
        """).strip()

        suggestions = [
            {
                "line": 2,
                "fix": fix
            }
        ]

        result = ASTRewriter.rewrite(source, suggestions)
        # We expect indentation to be handled
        expected = textwrap.dedent("""
            def foo():
                x = [
                    1,
                    2
                ]
        """).strip()

        assert result == expected

    def test_multiple_replacements(self):
        source = textwrap.dedent("""
            def foo():
                a = 1
                b = 2
                c = 3
        """).strip()

        # Replace a=1 with a=10
        # Replace c=3 with c=30

        suggestions = [
            {"line": 2, "fix": "a = 10"},
            {"line": 4, "fix": "c = 30"}
        ]

        result = ASTRewriter.rewrite(source, suggestions)
        expected = textwrap.dedent("""
            def foo():
                a = 10
                b = 2
                c = 30
        """).strip()

        assert result == expected

    def test_invalid_syntax_in_fix(self):
        source = "x = 1"
        suggestions = [
            {"line": 1, "fix": "x ="} # Syntax error
        ]
        # Should skip
        result = ASTRewriter.rewrite(source, suggestions)
        assert result == source

    def test_node_not_found(self):
        source = "x = 1"
        suggestions = [
            {"line": 100, "fix": "x = 2"} # Line out of bounds
        ]
        # Should skip
        result = ASTRewriter.rewrite(source, suggestions)
        assert result == source

    def test_preserves_comments(self):
        source = textwrap.dedent("""
            # Header comment
            def foo():
                x = 1  # Inline comment
                # Another comment
                y = 2
        """).strip()

        # Replace y=2 with y=3
        suggestions = [
            {"line": 5, "fix": "y = 3"}
        ]

        result = ASTRewriter.rewrite(source, suggestions)

        expected = textwrap.dedent("""
            # Header comment
            def foo():
                x = 1  # Inline comment
                # Another comment
                y = 3
        """).strip()

        assert result == expected
