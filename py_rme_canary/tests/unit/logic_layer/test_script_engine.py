"""Tests for the ScriptEngine sandbox."""
from unittest.mock import Mock

import pytest

from py_rme_canary.logic_layer.script_engine import ScriptEngine, ScriptStatus


@pytest.fixture
def engine() -> ScriptEngine:
    mock_map = Mock()
    mock_map.width = 100
    mock_map.height = 100
    return ScriptEngine(game_map=mock_map)


def test_safe_script_execution(engine: ScriptEngine) -> None:
    script = """
result = 1 + 1
"""
    result = engine.execute(script)
    assert result.success
    assert result.return_value == 2


def test_blocked_imports(engine: ScriptEngine) -> None:
    script = "import os"
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Import not allowed" in result.error


def test_blocked_dict_access(engine: ScriptEngine) -> None:
    script = "x = {}; print(x.__dict__)"
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access" in result.error
    assert "__dict__" in result.error


def test_blocked_class_access(engine: ScriptEngine) -> None:
    script = "x = 1; print(x.__class__)"
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access" in result.error
    assert "__class__" in result.error


def test_blocked_format_method(engine: ScriptEngine) -> None:
    script = "'{0.__class__}'.format(1)"
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden method: format" in result.error


def test_blocked_format_method_on_variable(engine: ScriptEngine) -> None:
    script = "s = '{0}'; s.format(1)"
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden method: format" in result.error


def test_blocked_format_map(engine: ScriptEngine) -> None:
    script = "s = '{0}'; s.format_map({0: 1})"
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden method: format_map" in result.error


def test_allowed_math_module(engine: ScriptEngine) -> None:
    script = "import math; result = math.sqrt(4)"
    result = engine.execute(script)
    assert result.success
    assert result.return_value == 2.0
