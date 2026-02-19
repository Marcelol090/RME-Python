from __future__ import annotations

from py_rme_canary.logic_layer.hotkey_manager import Hotkey, HotkeyManager


def test_hotkey_manager_persists_brush_and_position(tmp_path) -> None:
    mgr = HotkeyManager(config_dir=tmp_path)
    mgr.set_hotkey(1, Hotkey.from_brush("Stone Wall"))
    mgr.set_hotkey(0, Hotkey.from_position(128, 256, 7))
    mgr.save()

    loaded = HotkeyManager(config_dir=tmp_path)
    loaded.load()

    hk_brush = loaded.get_hotkey(1)
    assert hk_brush.is_brush is True
    assert hk_brush.brush_name == "Stone Wall"

    hk_pos = loaded.get_hotkey(0)
    assert hk_pos.is_position is True
    assert hk_pos.position.x == 128
    assert hk_pos.position.y == 256
    assert hk_pos.position.z == 7


def test_hotkey_manager_invalid_slot_returns_empty() -> None:
    mgr = HotkeyManager()
    empty = mgr.get_hotkey(99)
    assert empty.is_empty is True
