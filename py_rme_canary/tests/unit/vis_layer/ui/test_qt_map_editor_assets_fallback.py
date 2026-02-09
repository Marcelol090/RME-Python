from __future__ import annotations

from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_assets import QtMapEditorAssetsMixin


class _DummyMapper:
    def __init__(self, mapping: dict[int, int]) -> None:
        self._mapping = dict(mapping)

    def get_client_id(self, server_id: int) -> int | None:
        return self._mapping.get(int(server_id))


class _DummyEditor(QtMapEditorAssetsMixin):
    def __init__(self) -> None:
        self.id_mapper = None
        self.appearance_assets = None
        self.client_version = 0
        self.asset_profile = None
        self.sprite_assets = object()
        self._sprite_render_temporarily_disabled = False


def test_candidate_sprite_ids_include_mapper_and_server_fallback() -> None:
    editor = _DummyEditor()
    editor.id_mapper = _DummyMapper({100: 300})

    assert editor._candidate_sprite_ids_for_server_id(100) == [300, 100]


def test_candidate_sprite_ids_work_without_mapper() -> None:
    editor = _DummyEditor()
    editor.id_mapper = None

    assert editor._candidate_sprite_ids_for_server_id(2050) == [2050]


def test_sprite_render_enabled_without_mapper() -> None:
    editor = _DummyEditor()
    editor.id_mapper = None

    assert editor._sprite_render_enabled() is True
