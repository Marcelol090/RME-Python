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
        try:
            raw = self._settings.value("preferences/auto_load_appearances", True)
        except Exception:
            return True
        if isinstance(raw, bool):
            return bool(raw)
        if isinstance(raw, (int, float)):
            return bool(raw)
        value = str(raw).strip().lower()
        return value not in ("0", "false", "no", "off", "")

    def set_auto_load_appearances(self, value: bool) -> None:
        self._settings.setValue("preferences/auto_load_appearances", bool(value))
        self._settings.sync()

    def get_sprite_match_on_paste(self) -> bool:
        """Get sprite match on paste preference for cross-version copy/paste."""
        try:
            raw = self._settings.value("preferences/sprite_match_on_paste", True)
        except Exception:
            return True
        if isinstance(raw, bool):
            return bool(raw)
        if isinstance(raw, (int, float)):
            return bool(raw)
        value = str(raw).strip().lower()
        return value not in ("0", "false", "no", "off", "")

    def set_sprite_match_on_paste(self, value: bool) -> None:
        """Set sprite match on paste preference."""
        self._settings.setValue("preferences/sprite_match_on_paste", bool(value))
        self._settings.sync()

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
