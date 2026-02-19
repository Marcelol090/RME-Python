from __future__ import annotations

from py_rme_canary.vis_layer.ui.main_window import qt_map_editor_modern_ux as modern_ux_module


class _FakeMenu:
    def __init__(self) -> None:
        self.add_menu_calls = 0

    def addMenu(self, _label: str):  # noqa: N802 - Qt naming parity for test double
        self.add_menu_calls += 1
        return _FakeMenu()


class _DummyEditor(modern_ux_module.QtMapEditorModernUXMixin):
    def __init__(self, *, with_recent_menu: bool) -> None:
        self.menu_file = _FakeMenu()
        if with_recent_menu:
            self.menu_recent_files = _FakeMenu()

    def _open_recent_file(self, _path: str) -> None:
        return None


def test_setup_recent_files_reuses_existing_menu(monkeypatch) -> None:
    called: dict[str, int] = {"count": 0}

    def _fake_build(menu, on_file_selected) -> None:  # noqa: ANN001
        assert menu is not None
        assert callable(on_file_selected)
        called["count"] += 1

    monkeypatch.setattr(modern_ux_module, "build_recent_files_menu", _fake_build)
    editor = _DummyEditor(with_recent_menu=True)

    editor._setup_recent_files()

    assert called["count"] == 1
    assert editor.menu_file.add_menu_calls == 0


def test_setup_recent_files_falls_back_to_file_menu_when_missing(monkeypatch) -> None:
    called: dict[str, int] = {"count": 0}

    def _fake_build(menu, on_file_selected) -> None:  # noqa: ANN001
        assert menu is not None
        assert callable(on_file_selected)
        called["count"] += 1

    monkeypatch.setattr(modern_ux_module, "build_recent_files_menu", _fake_build)
    editor = _DummyEditor(with_recent_menu=False)

    editor._setup_recent_files()

    assert called["count"] == 1
    assert editor.menu_file.add_menu_calls == 1
    assert hasattr(editor, "menu_recent_files")
