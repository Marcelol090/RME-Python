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


class _DummyAppearanceIndex:
    def __init__(self, mapping: dict[tuple[str, int], int | None]) -> None:
        self._mapping = dict(mapping)

    def get_sprite_id(
        self,
        appearance_id: int,
        *,
        kind: str = "object",
        time_ms: int | None = None,
        seed: int | None = None,
    ) -> int | None:
        _ = (time_ms, seed)
        return self._mapping.get((str(kind), int(appearance_id)))


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


def test_candidate_sprite_ids_support_raw_client_id_encoding() -> None:
    editor = _DummyEditor()
    editor.id_mapper = _DummyMapper({300: 9000})  # Should be ignored for raw client-id path.
    editor.appearance_assets = _DummyAppearanceIndex({("object", 300): 4444})

    assert editor._candidate_sprite_ids_for_server_id(-300) == [4444, 300]


def test_resolve_sprite_id_falls_back_across_appearance_kinds() -> None:
    editor = _DummyEditor()
    editor.appearance_assets = _DummyAppearanceIndex(
        {
            ("object", 7500): None,
            ("outfit", 7500): None,
            ("effect", 7500): 61234,
            ("missile", 7500): None,
        }
    )

    assert editor._resolve_sprite_id_from_client_id(7500) == 61234
