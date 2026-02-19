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
        {"name": "A", "client_version": 860, "assets_dir": "test_data/a", "preferred_kind": "legacy"},
        {"name": "", "client_version": 0, "assets_dir": "test_data/invalid"},
        "invalid",
        {"name": "B", "client_version": 1310, "assets_dir": "test_data/b", "preferred_kind": "modern"},
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


def test_user_settings_persists_preferences_fields() -> None:
    org = "py_rme_canary_tests"
    app = f"preferences_{uuid4().hex}"

    settings = UserSettings(org=org, app=app)
    settings.set_show_welcome_dialog(False)
    settings.set_always_make_backup(False)
    settings.set_check_updates_on_startup(True)
    settings.set_only_one_instance(False)
    settings.set_enable_tileset_editing(True)
    settings.set_use_old_item_properties_window(True)
    settings.set_undo_queue_size(2048)
    settings.set_undo_max_memory_mb(512)
    settings.set_worker_threads(8)
    settings.set_replace_count_limit(25000)
    settings.set_delete_backup_days(21)
    settings.set_copy_position_format(3)
    settings.set_theme_name("glass_8bit")
    settings.set_show_grid_default(False)
    settings.set_show_tooltips_default(False)
    settings.set_default_brush_size(4)
    settings.set_automagic_default(False)
    settings.set_eraser_leave_unique(False)
    settings.set_merge_paste_default(True)
    settings.set_merge_move_default(True)
    settings.set_borderize_paste_default(False)
    settings.set_switch_mouse_buttons(True)
    settings.set_double_click_properties(False)
    settings.set_inversed_scroll(True)
    settings.set_scroll_speed(70)
    settings.set_zoom_speed(40)
    settings.set_palette_style("terrain", 1)
    settings.set_palette_style("collection", 2)

    loaded = UserSettings(org=org, app=app)
    assert loaded.get_show_welcome_dialog() is False
    assert loaded.get_always_make_backup() is False
    assert loaded.get_check_updates_on_startup() is True
    assert loaded.get_only_one_instance() is False
    assert loaded.get_enable_tileset_editing() is True
    assert loaded.get_use_old_item_properties_window() is True
    assert loaded.get_undo_queue_size() == 2048
    assert loaded.get_undo_max_memory_mb() == 512
    assert loaded.get_worker_threads() == 8
    assert loaded.get_replace_count_limit() == 25000
    assert loaded.get_delete_backup_days() == 21
    assert loaded.get_copy_position_format() == 3
    assert loaded.get_theme_name() == "glass_8bit"
    assert loaded.get_show_grid_default() is False
    assert loaded.get_show_tooltips_default() is False
    assert loaded.get_default_brush_size() == 4
    assert loaded.get_automagic_default() is False
    assert loaded.get_eraser_leave_unique() is False
    assert loaded.get_merge_paste_default() is True
    assert loaded.get_merge_move_default() is True
    assert loaded.get_borderize_paste_default() is False
    assert loaded.get_switch_mouse_buttons() is True
    assert loaded.get_double_click_properties() is False
    assert loaded.get_inversed_scroll() is True
    assert loaded.get_scroll_speed() == 70
    assert loaded.get_zoom_speed() == 40
    assert loaded.get_palette_style("terrain") == 1
    assert loaded.get_palette_style("collection") == 2
