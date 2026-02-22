"""Tests for hardened ScriptEngine security."""
import pytest
from py_rme_canary.logic_layer.script_engine import ScriptEngine, ScriptStatus

from unittest.mock import Mock

@pytest.fixture
def engine() -> ScriptEngine:
    mock_map = Mock()
    mock_map.width = 100
    mock_map.height = 100
    return ScriptEngine(game_map=mock_map)

def test_blocked_generator_frame_access(engine: ScriptEngine) -> None:
    # Attempt to access frame via generator
    script = """
def gen():
    yield 1
g = gen()
f = g.gi_frame
"""
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access" in result.error
    assert "gi_frame" in result.error

def test_blocked_frame_back_access(engine: ScriptEngine) -> None:
    # Attempt to walk up the stack
    script = """
def foo():
    pass
# Assuming we could get a frame object, f_back should be blocked
# This is harder to test directly without a way to get a frame first,
# but we can test that the attribute access itself is blocked in AST.
x = lambda: None
y = x.f_back
"""
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access" in result.error
    assert "f_back" in result.error

def test_blocked_frame_globals_access(engine: ScriptEngine) -> None:
    script = """
x = lambda: None
y = x.f_globals
"""
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access" in result.error
    assert "f_globals" in result.error

def test_blocked_method_func_access(engine: ScriptEngine) -> None:
    script = """
class A:
    def m(self): pass
a = A()
f = a.m.__func__
"""
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access" in result.error
    assert "__func__" in result.error

def test_blocked_method_self_access(engine: ScriptEngine) -> None:
    script = """
class A:
    def m(self): pass
a = A()
s = a.m.__self__
"""
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access" in result.error
    assert "__self__" in result.error

def test_blocked_traceback_access(engine: ScriptEngine) -> None:
    script = """
try:
    1/0
except Exception as e:
    tb = e.__traceback__
"""
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access" in result.error
    assert "__traceback__" in result.error
