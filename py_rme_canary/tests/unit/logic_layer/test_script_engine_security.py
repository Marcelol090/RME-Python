
"""Security tests for ScriptEngine sandbox."""

from unittest.mock import Mock

import pytest

from py_rme_canary.logic_layer.script_engine import ScriptEngine, ScriptStatus

@pytest.fixture
def engine() -> ScriptEngine:
    mock_map = Mock()
    mock_map.width = 100
    mock_map.height = 100
    return ScriptEngine(game_map=mock_map)

def test_blocked_generator_frame(engine: ScriptEngine) -> None:
    """Test that access to generator frame (gi_frame) is blocked."""
    script = """
def g(): yield 1
gen = g()
f = gen.gi_frame
"""
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access: gi_frame" in result.error

def test_blocked_coroutine_frame(engine: ScriptEngine) -> None:
    """Test that access to coroutine frame (cr_frame) is blocked."""
    # Note: async/await syntax is blocked by AST visitor too, but attribute access should also be blocked.
    script = """
async def c(): pass
co = c()
f = co.cr_frame
"""
    # This might fail due to async syntax being blocked first.
    # But let's check attribute access specifically.
    result = engine.execute(script)
    # Could be blocked by AsyncFunctionDef or Attribute access.
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden" in result.error

def test_blocked_frame_attributes(engine: ScriptEngine) -> None:
    """Test that frame attributes are blocked if a frame is obtained."""
    # We can't easily get a frame, so we simulate attribute access on an object.
    script = """
class MockFrame:
    f_globals = {}

f = MockFrame()
g = f.f_globals
"""
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access: f_globals" in result.error

def test_blocked_traceback_frame(engine: ScriptEngine) -> None:
    """Test that traceback frame access is blocked."""
    script = """
try:
    1/0
except:
    # We can't catch exception object easily, but if we could...
    pass

# Simulate access
class MockTb:
    tb_frame = None

t = MockTb()
f = t.tb_frame
"""
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access: tb_frame" in result.error

def test_blocked_method_attributes(engine: ScriptEngine) -> None:
    """Test that method attributes (__func__, __self__) are blocked."""
    script = """
class A:
    def m(self): pass

a = A()
m = a.m
f = m.__func__
"""
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access: __func__" in result.error
