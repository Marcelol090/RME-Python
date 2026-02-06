from __future__ import annotations

from threading import Lock

from PyQt6.QtCore import QSettings

from py_rme_canary.core.config.client_profiles import (
    ClientProfile,
    dump_client_profiles,
    parse_client_profiles,
    resolve_active_client_profile,
)

_DEFAULT_ORG = "py_rme_canary"
_DEFAULT_APP = "py_rme_canary"


class UserSettings:
    """Simple persisted user preferences wrapper around QSettings."""

    def __init__(self, *, org: str = _DEFAULT_ORG, app: str = _DEFAULT_APP) -> None:
        self._settings = QSettings(org, app)

    def _pref_key(self, name: str) -> str:
        return f"preferences/{name}"

    def _get_bool_pref(self, name: str, default: bool) -> bool:
        try:
            raw = self._settings.value(self._pref_key(name), default)
        except Exception:
            return bool(default)
        if isinstance(raw, bool):
            return bool(raw)
        if isinstance(raw, (int, float)):
            return bool(raw)
        value = str(raw).strip().lower()
        return value not in ("0", "false", "no", "off", "")

    def _set_bool_pref(self, name: str, value: bool) -> None:
        self._settings.setValue(self._pref_key(name), bool(value))
        self._settings.sync()

    def _get_int_pref(self, name: str, default: int) -> int:
        try:
            return int(self._settings.value(self._pref_key(name), int(default)))
        except Exception:
            return int(default)

    def _set_int_pref(self, name: str, value: int) -> None:
        self._settings.setValue(self._pref_key(name), int(value))
        self._settings.sync()

    def get_default_client_version(self) -> int:
        try:
            return int(self._settings.value("preferences/default_client_version", 0))
        except Exception:
            return 0

    def set_default_client_version(self, value: int) -> None:
        self._settings.setValue("preferences/default_client_version", int(value))
        self._settings.sync()

    def get_client_assets_folder(self) -> str:
        try:
            return str(self._settings.value("preferences/client_assets_folder", "") or "")
        except Exception:
            return ""

    def set_client_assets_folder(self, value: str) -> None:
        self._settings.setValue("preferences/client_assets_folder", str(value or ""))
        self._settings.sync()

    def get_auto_load_appearances(self) -> bool:
        return self._get_bool_pref("auto_load_appearances", True)

    def set_auto_load_appearances(self, value: bool) -> None:
        self._set_bool_pref("auto_load_appearances", bool(value))

    def get_sprite_match_on_paste(self) -> bool:
        """Get sprite match on paste preference for cross-version copy/paste."""
        return self._get_bool_pref("sprite_match_on_paste", True)

    def set_sprite_match_on_paste(self, value: bool) -> None:
        """Set sprite match on paste preference."""
        self._set_bool_pref("sprite_match_on_paste", bool(value))

    def get_show_welcome_dialog(self) -> bool:
        return self._get_bool_pref("show_welcome_dialog", True)

    def set_show_welcome_dialog(self, value: bool) -> None:
        self._set_bool_pref("show_welcome_dialog", bool(value))

    def get_always_make_backup(self) -> bool:
        return self._get_bool_pref("always_make_backup", True)

    def set_always_make_backup(self, value: bool) -> None:
        self._set_bool_pref("always_make_backup", bool(value))

    def get_check_updates_on_startup(self) -> bool:
        return self._get_bool_pref("check_updates_on_startup", False)

    def set_check_updates_on_startup(self, value: bool) -> None:
        self._set_bool_pref("check_updates_on_startup", bool(value))

    def get_only_one_instance(self) -> bool:
        return self._get_bool_pref("only_one_instance", True)

    def set_only_one_instance(self, value: bool) -> None:
        self._set_bool_pref("only_one_instance", bool(value))

    def get_enable_tileset_editing(self) -> bool:
        return self._get_bool_pref("enable_tileset_editing", False)

    def set_enable_tileset_editing(self, value: bool) -> None:
        self._set_bool_pref("enable_tileset_editing", bool(value))

    def get_use_old_item_properties_window(self) -> bool:
        return self._get_bool_pref("use_old_item_properties_window", False)

    def set_use_old_item_properties_window(self, value: bool) -> None:
        self._set_bool_pref("use_old_item_properties_window", bool(value))

    def get_undo_queue_size(self) -> int:
        return self._get_int_pref("undo_queue_size", 1000)

    def set_undo_queue_size(self, value: int) -> None:
        self._set_int_pref("undo_queue_size", int(value))

    def get_undo_max_memory_mb(self) -> int:
        return self._get_int_pref("undo_max_memory_mb", 256)

    def set_undo_max_memory_mb(self, value: int) -> None:
        self._set_int_pref("undo_max_memory_mb", int(value))

    def get_worker_threads(self) -> int:
        return self._get_int_pref("worker_threads", 4)

    def set_worker_threads(self, value: int) -> None:
        self._set_int_pref("worker_threads", int(value))

    def get_replace_count_limit(self) -> int:
        return self._get_int_pref("replace_count_limit", 10000)

    def set_replace_count_limit(self, value: int) -> None:
        self._set_int_pref("replace_count_limit", int(value))

    def get_delete_backup_days(self) -> int:
        return self._get_int_pref("delete_backup_days", 7)

    def set_delete_backup_days(self, value: int) -> None:
        self._set_int_pref("delete_backup_days", int(value))

    def get_copy_position_format(self) -> int:
        return self._get_int_pref("copy_position_format", 0)

    def set_copy_position_format(self, value: int) -> None:
        self._set_int_pref("copy_position_format", int(value))

    def get_client_profiles(self) -> list[ClientProfile]:
        """Get all persisted client profiles."""
        try:
            raw = self._settings.value("profiles/client_profiles_v1", "[]")
        except Exception:
            return []
        return parse_client_profiles(raw)

    def set_client_profiles(self, profiles: list[ClientProfile]) -> None:
        """Persist client profiles to settings."""
        payload = dump_client_profiles(profiles)
        self._settings.setValue("profiles/client_profiles_v1", payload)
        self._settings.sync()

    def get_active_client_profile_id(self) -> str:
        """Get active profile id."""
        try:
            return str(self._settings.value("profiles/active_client_profile_id", "") or "")
        except Exception:
            return ""

    def set_active_client_profile_id(self, profile_id: str) -> None:
        """Persist active profile id."""
        self._settings.setValue("profiles/active_client_profile_id", str(profile_id or ""))
        self._settings.sync()

    def get_active_client_profile(self, *, client_version: int | None = None) -> ClientProfile | None:
        """Resolve active profile from stored id and optional version hint."""
        profiles = self.get_client_profiles()
        active_id = self.get_active_client_profile_id()
        return resolve_active_client_profile(
            profiles=profiles,
            active_profile_id=active_id,
            client_version=client_version,
        )


_settings_lock = Lock()
_settings_instance: UserSettings | None = None


def get_user_settings() -> UserSettings:
    """Return a shared UserSettings instance."""
    global _settings_instance
    if _settings_instance is None:
        with _settings_lock:
            if _settings_instance is None:
                _settings_instance = UserSettings()
    return _settings_instance
