from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("PyQt6")

from py_rme_canary.core.config.client_profiles import ClientProfile
from py_rme_canary.vis_layer.ui.dialogs.client_data_loader_dialog import ClientDataLoadConfig
from py_rme_canary.vis_layer.ui.main_window import qt_map_editor_assets as assets_module
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_assets import QtMapEditorAssetsMixin


@pytest.fixture
def app():
    from PyQt6.QtWidgets import QApplication

    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


class _FakeSettings:
    def __init__(self) -> None:
        self.assets_folder = ""
        self.default_client_version = 0

    def set_client_assets_folder(self, path: str) -> None:
        self.assets_folder = str(path)

    def set_default_client_version(self, version: int) -> None:
        self.default_client_version = int(version)


class _DummyEditor(QtMapEditorAssetsMixin):
    def __init__(self) -> None:
        self.client_version = 0
        self.engine = ""
        self.assets_selection_path = ""
        self.sprite_assets = None
        self.appearance_assets = None
        self.id_mapper = None
        self.status_messages: list[str] = []
        self.refresh_calls = 0
        self.status = SimpleNamespace(showMessage=lambda msg: self.status_messages.append(str(msg)))

    def _apply_asset_profile(self, _profile):
        self.sprite_assets = SimpleNamespace(sprite_count=256)
        return SimpleNamespace()

    def _reload_item_definitions_for_current_context(self, *, source: str):
        self.status_messages.append(f"reload:{source}")
        self.id_mapper = SimpleNamespace(server_to_client={100: 200})
        return []

    def _refresh_after_asset_data_load(self) -> None:
        self.refresh_calls += 1

    def _build_client_data_load_summary(
        self,
        *,
        profile,
        warnings: list[str],
        mapping_count: int,
        explicit_counts: dict[str, int],
        source: str,
    ) -> str:
        kind = str(getattr(profile, "kind", "unknown"))
        return f"summary:{kind}:{mapping_count}:{source}:{len(warnings)}:{len(explicit_counts)}"

    def _update_status_capabilities(self, *, prefix: str) -> None:
        self.status_messages.append(str(prefix))


class _FakeProgress:
    created: list["_FakeProgress"] = []

    def __init__(self, *_args, **_kwargs) -> None:
        self.labels: list[str] = []
        self.values: list[int] = []
        self.closed = False
        self.__class__.created.append(self)

    def setWindowTitle(self, *_args) -> None:
        return None

    def setWindowModality(self, *_args) -> None:
        return None

    def setAutoClose(self, *_args) -> None:
        return None

    def setMinimumDuration(self, *_args) -> None:
        return None

    def setLabelText(self, message: str) -> None:
        self.labels.append(str(message))

    def setValue(self, value: int) -> None:
        self.values.append(int(value))

    def wasCanceled(self) -> bool:
        return False

    def close(self) -> None:
        self.closed = True


def test_load_client_data_stack_appends_saved_profile_to_summary(app, monkeypatch) -> None:
    editor = _DummyEditor()
    settings = _FakeSettings()
    _FakeProgress.created.clear()
    info_messages: list[str] = []
    critical_messages: list[str] = []

    config = ClientDataLoadConfig(
        assets_path="C:/clients/1098",
        prefer_kind="legacy",
        client_version_hint=1098,
        items_otb_path="",
        items_xml_path="",
        show_summary=True,
    )
    profile = SimpleNamespace(kind="legacy", assets_dir="C:/clients/1098", root="C:/clients/1098")
    saved_profile = ClientProfile(
        profile_id="profile-1098",
        name="Legacy 10.98",
        client_version=1098,
        assets_dir="C:/clients/1098",
        preferred_kind="legacy",
    )

    monkeypatch.setattr(assets_module, "QProgressDialog", _FakeProgress)
    monkeypatch.setattr(assets_module, "get_user_settings", lambda: settings)
    monkeypatch.setattr(assets_module, "detect_asset_profile", lambda *_a, **_k: profile)
    monkeypatch.setattr(editor, "_maybe_save_loaded_client_profile", lambda **_k: saved_profile)
    monkeypatch.setattr(
        assets_module.QMessageBox,
        "information",
        staticmethod(lambda _parent, _title, text: info_messages.append(str(text))),
    )
    monkeypatch.setattr(
        assets_module.QMessageBox,
        "critical",
        staticmethod(lambda _parent, _title, text: critical_messages.append(str(text))),
    )

    editor._load_client_data_stack(config, source="interactive_loader")

    assert not critical_messages
    assert info_messages
    assert "summary:legacy:1:interactive_loader:0:0" in info_messages[0]
    assert "Profile saved: Legacy 10.98 (profile-1098)" in info_messages[0]
    assert settings.assets_folder == "C:/clients/1098"
    assert settings.default_client_version == 1098
    assert editor.refresh_calls == 1
    assert "Client data stack loaded" in editor.status_messages

    progress = _FakeProgress.created[-1]
    assert progress.closed
    assert progress.values == [0, 1, 2, 3, 4, 5]
    assert "Loading item definitions (items.otb / items.xml)..." in progress.labels


def test_load_client_data_stack_uses_explicit_definition_paths_when_provided(app, monkeypatch) -> None:
    editor = _DummyEditor()
    settings = _FakeSettings()
    _FakeProgress.created.clear()
    info_messages: list[str] = []
    explicit_calls: list[tuple[object, object]] = []

    config = ClientDataLoadConfig(
        assets_path="C:/clients/1098",
        prefer_kind="legacy",
        client_version_hint=1098,
        items_otb_path="C:/defs/items.otb",
        items_xml_path="C:/defs/items.xml",
        show_summary=True,
    )
    profile = SimpleNamespace(kind="legacy", assets_dir="C:/clients/1098", root="C:/clients/1098")

    monkeypatch.setattr(assets_module, "QProgressDialog", _FakeProgress)
    monkeypatch.setattr(assets_module, "get_user_settings", lambda: settings)
    monkeypatch.setattr(assets_module, "detect_asset_profile", lambda *_a, **_k: profile)
    monkeypatch.setattr(editor, "_maybe_save_loaded_client_profile", lambda **_k: None)
    monkeypatch.setattr(
        assets_module.QMessageBox,
        "information",
        staticmethod(lambda _parent, _title, text: info_messages.append(str(text))),
    )
    monkeypatch.setattr(assets_module.QMessageBox, "critical", staticmethod(lambda *_a, **_k: None))

    def _load_explicit(*, items_otb_path, items_xml_path):
        explicit_calls.append((items_otb_path, items_xml_path))
        mapper = SimpleNamespace(server_to_client={1: 1001, 2: 1002})
        return mapper, ["warn:explicit"], {"items_xml_count": 2, "items_otb_count": 2}

    monkeypatch.setattr(editor, "_load_item_definitions_from_explicit_paths", _load_explicit)
    monkeypatch.setattr(editor, "_set_id_mapper", lambda mapper: setattr(editor, "id_mapper", mapper))

    editor._load_client_data_stack(config, source="interactive_loader")

    assert explicit_calls
    assert len(explicit_calls) == 1
    otb_path, xml_path = explicit_calls[0]
    assert str(otb_path).endswith("items.otb")
    assert str(xml_path).endswith("items.xml")
    assert info_messages
    assert "summary:legacy:2:interactive_loader:1:2" in info_messages[0]
