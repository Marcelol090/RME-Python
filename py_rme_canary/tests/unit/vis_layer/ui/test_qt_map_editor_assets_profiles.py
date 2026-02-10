from __future__ import annotations

from types import SimpleNamespace

from py_rme_canary.core.config.client_profiles import ClientProfile
from py_rme_canary.vis_layer.ui.dialogs.client_data_loader_dialog import ClientDataLoadConfig
from py_rme_canary.vis_layer.ui.main_window import qt_map_editor_assets as assets_module
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_assets import QtMapEditorAssetsMixin


class _FakeSettings:
    def __init__(self, profiles: list[ClientProfile] | None = None) -> None:
        self._profiles = list(profiles or [])
        self.active_profile_id = ""

    def get_client_profiles(self) -> list[ClientProfile]:
        return list(self._profiles)

    def set_client_profiles(self, profiles: list[ClientProfile]) -> None:
        self._profiles = list(profiles)

    def set_active_client_profile_id(self, profile_id: str) -> None:
        self.active_profile_id = str(profile_id)


class _DummyEditor(QtMapEditorAssetsMixin):
    def __init__(self) -> None:
        self.client_version = 1098


def test_should_offer_profile_save_only_for_interactive_source() -> None:
    cfg = ClientDataLoadConfig(
        assets_path="C:/clients/1098",
        prefer_kind="legacy",
        client_version_hint=1098,
        items_otb_path="",
        items_xml_path="",
        show_summary=True,
    )

    assert _DummyEditor._should_offer_profile_save(config=cfg, source="interactive_loader") is True
    assert _DummyEditor._should_offer_profile_save(config=cfg, source="manual_assets_dir") is False


def test_suggest_profile_name_uses_version_kind_and_folder() -> None:
    editor = _DummyEditor()
    cfg = ClientDataLoadConfig(
        assets_path="C:/clients/1098",
        prefer_kind="legacy",
        client_version_hint=1098,
        items_otb_path="",
        items_xml_path="",
        show_summary=True,
    )

    suggested = editor._suggest_profile_name(config=cfg, profile=SimpleNamespace(kind="legacy"))
    assert suggested == "1098-legacy-1098"


def test_save_client_profile_adds_new_profile(monkeypatch) -> None:
    editor = _DummyEditor()
    fake_settings = _FakeSettings()
    monkeypatch.setattr(assets_module, "get_user_settings", lambda: fake_settings)

    cfg = ClientDataLoadConfig(
        assets_path="C:/clients/1098",
        prefer_kind="legacy",
        client_version_hint=1098,
        items_otb_path="",
        items_xml_path="",
        show_summary=True,
    )
    saved = editor._save_client_profile(
        profile_name="My 10.98",
        config=cfg,
        profile=SimpleNamespace(kind="legacy"),
    )

    assert saved is not None
    assert saved.name == "My 10.98"
    assert len(fake_settings.get_client_profiles()) == 1
    assert fake_settings.active_profile_id == saved.profile_id


def test_save_client_profile_updates_existing_match(monkeypatch) -> None:
    editor = _DummyEditor()
    existing = ClientProfile(
        profile_id="existing-1098",
        name="Old Name",
        client_version=1098,
        assets_dir="C:/clients/1098",
        preferred_kind="legacy",
    )
    fake_settings = _FakeSettings([existing])
    monkeypatch.setattr(assets_module, "get_user_settings", lambda: fake_settings)

    cfg = ClientDataLoadConfig(
        assets_path="C:/clients/1098",
        prefer_kind="legacy",
        client_version_hint=1098,
        items_otb_path="",
        items_xml_path="",
        show_summary=True,
    )
    saved = editor._save_client_profile(
        profile_name="Updated Name",
        config=cfg,
        profile=SimpleNamespace(kind="legacy"),
    )

    assert saved is not None
    assert saved.profile_id == "existing-1098"
    assert saved.name == "Updated Name"
    assert len(fake_settings.get_client_profiles()) == 1
