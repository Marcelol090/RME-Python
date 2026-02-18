
import pytest
import textwrap
from py_rme_canary.logic_layer.script_engine import ScriptEngine, ScriptStatus
from py_rme_canary.core.data.gamemap import GameMap, MapHeader

@pytest.fixture
def engine():
    header = MapHeader(otbm_version=1, width=100, height=100)
    game_map = GameMap(header=header)
    return ScriptEngine(game_map)

def test_block_generator_frame_access(engine):
    script = textwrap.dedent("""
    g = (x for x in range(1))
    f = g.gi_frame
    """)
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access: gi_frame" in result.error

def test_block_coroutine_frame_access(engine):
    script = textwrap.dedent("""
    async def foo(): pass
    c = foo()
    f = c.cr_frame
    """)
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access: cr_frame" in result.error

def test_block_traceback_frame_access(engine):
    script = textwrap.dedent("""
    try:
        raise Exception("test")
    except Exception as e:
        tb = e.__traceback__
        f = tb.tb_frame
    """)
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access: tb_frame" in result.error

def test_block_frame_attributes(engine):
    script = textwrap.dedent("""
    class FakeFrame:
        pass
    f = FakeFrame()
    x = f.f_back
    """)
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access: f_back" in result.error

    script = textwrap.dedent("""
    class FakeFrame:
        pass
    f = FakeFrame()
    x = f.f_globals
    """)
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access: f_globals" in result.error

def test_block_method_internals(engine):
    script = textwrap.dedent("""
    def foo(): pass
    x = foo.__code__
    """)
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access: __code__" in result.error

    script = textwrap.dedent("""
    class A:
        def foo(self): pass
    a = A()
    x = a.foo.__func__
    """)
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access: __func__" in result.error

    script = textwrap.dedent("""
    class A:
        def foo(self): pass
    a = A()
    x = a.foo.__self__
    """)
    result = engine.execute(script)
    assert result.status == ScriptStatus.SECURITY_ERROR
    assert "Forbidden attribute access: __self__" in result.error
