from __future__ import annotations

from uuid import uuid4

from py_rme_canary.core.config.client_profiles import (
    ClientProfile,
    create_client_profile,
    dump_client_profiles,
    parse_client_profiles,
    resolve_active_client_profile,
)
from py_rme_canary.core.config.user_settings import UserSettings


def test_create_profile_generates_unique_ids() -> None:
    first = create_client_profile(
        name="10.98 Custom",
        client_version=1098,
        assets_dir="C:/assets/1098",
        existing_ids=set(),
    )
    second = create_client_profile(
        name="10.98 Custom",
        client_version=1098,
        assets_dir="C:/assets/1098b",
        existing_ids={first.profile_id},
    )
    assert first.profile_id == "10-98-custom"
    assert second.profile_id == "10-98-custom-2"


def test_parse_profiles_ignores_invalid_entries() -> None:
    raw = [
        {"name": "A", "client_version": 860, "assets_dir": "/tmp/a", "preferred_kind": "legacy"},
        {"name": "", "client_version": 0, "assets_dir": "/tmp/invalid"},
        "invalid",
        {"name": "B", "client_version": 1310, "assets_dir": "/tmp/b", "preferred_kind": "modern"},
    ]
    profiles = parse_client_profiles(raw)
    assert [p.name for p in profiles] == ["A", "B"]


def test_dump_parse_roundtrip() -> None:
    profiles = [
        ClientProfile(
            profile_id="legacy-860",
            name="Legacy 8.60",
            client_version=860,
            assets_dir="C:/tibia/860",
            preferred_kind="legacy",
        ),
        ClientProfile(
            profile_id="modern-1310",
            name="Modern 13.10",
            client_version=1310,
            assets_dir="C:/tibia/1310",
            preferred_kind="modern",
        ),
    ]
    payload = dump_client_profiles(profiles)
    restored = parse_client_profiles(payload)
    assert restored == profiles


def test_resolve_active_profile_with_fallbacks() -> None:
    profiles = [
        ClientProfile("v860", "8.60", 860, "C:/a", "legacy"),
        ClientProfile("v1098", "10.98", 1098, "C:/b", "legacy"),
    ]
    assert resolve_active_client_profile(profiles=profiles, active_profile_id="v1098").profile_id == "v1098"
    assert (
        resolve_active_client_profile(profiles=profiles, active_profile_id="", client_version=860).profile_id == "v860"
    )
    assert resolve_active_client_profile(profiles=profiles, active_profile_id="missing").profile_id == "v860"


def test_user_settings_persists_client_profiles() -> None:
    org = "py_rme_canary_tests"
    app = f"profiles_{uuid4().hex}"
    settings = UserSettings(org=org, app=app)

    profiles = [
        create_client_profile(
            name="11.00 Vanilla",
            client_version=1100,
            assets_dir="C:/clients/1100",
            preferred_kind="auto",
            existing_ids=set(),
        ),
        create_client_profile(
            name="13.10 Custom",
            client_version=1310,
            assets_dir="C:/clients/1310-custom",
            preferred_kind="modern",
            existing_ids={"11-00-vanilla"},
        ),
    ]

    settings.set_client_profiles(profiles)
    settings.set_active_client_profile_id(profiles[1].profile_id)

    loaded = settings.get_client_profiles()
    assert loaded == profiles
    assert settings.get_active_client_profile_id() == profiles[1].profile_id
    assert settings.get_active_client_profile(client_version=1100).profile_id == profiles[1].profile_id

    settings.set_active_client_profile_id("")
    fallback = settings.get_active_client_profile(client_version=1100)
    assert fallback is not None
    assert fallback.client_version == 1100
