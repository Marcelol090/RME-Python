from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

_PROFILE_ID_ALLOWED = re.compile(r"[^a-z0-9]+")
_PREFERRED_KINDS = {"auto", "modern", "legacy"}


@dataclass(frozen=True, slots=True)
class ClientProfile:
    """Persisted client profile for assets loading."""

    profile_id: str
    name: str
    client_version: int
    assets_dir: str
    preferred_kind: str = "auto"


def normalize_preferred_kind(value: str | None) -> str:
    """Normalize preferred asset kind to supported values."""
    raw = str(value or "").strip().lower()
    if raw in _PREFERRED_KINDS:
        return raw
    return "auto"


def normalize_profile_id(value: str | None) -> str:
    """Normalize profile id to a filesystem/key-safe slug."""
    raw = str(value or "").strip().lower()
    normalized = _PROFILE_ID_ALLOWED.sub("-", raw).strip("-")
    return normalized or "profile"


def make_unique_profile_id(base_name: str, existing_ids: set[str]) -> str:
    """Build a stable unique profile id from the profile name."""
    base = normalize_profile_id(base_name)
    if base not in existing_ids:
        return base
    index = 2
    while True:
        candidate = f"{base}-{index}"
        if candidate not in existing_ids:
            return candidate
        index += 1


def create_client_profile(
    *,
    name: str,
    client_version: int,
    assets_dir: str,
    preferred_kind: str = "auto",
    profile_id: str | None = None,
    existing_ids: set[str] | None = None,
) -> ClientProfile:
    """Create a normalized profile with deterministic id generation."""
    normalized_name = str(name).strip()
    normalized_assets_dir = str(assets_dir or "").strip()
    if normalized_assets_dir.startswith("~"):
        normalized_assets_dir = str(Path(normalized_assets_dir).expanduser())
    normalized_kind = normalize_preferred_kind(preferred_kind)

    if not normalized_name:
        raise ValueError("Profile name cannot be empty.")
    if not normalized_assets_dir:
        raise ValueError("Assets directory cannot be empty.")

    known_ids = set(existing_ids or set())
    if profile_id:
        final_id = normalize_profile_id(profile_id)
    else:
        final_id = make_unique_profile_id(normalized_name, known_ids)

    return ClientProfile(
        profile_id=final_id,
        name=normalized_name,
        client_version=max(0, int(client_version)),
        assets_dir=normalized_assets_dir,
        preferred_kind=normalized_kind,
    )


def parse_client_profiles(raw: object) -> list[ClientProfile]:
    """Parse profiles from QSettings payloads safely."""
    payload: object = raw
    if isinstance(raw, str):
        try:
            payload = json.loads(raw)
        except Exception:
            payload = []
    if not isinstance(payload, list):
        return []

    profiles: list[ClientProfile] = []
    used_ids: set[str] = set()

    for entry in payload:
        if not isinstance(entry, dict):
            continue
        try:
            candidate = create_client_profile(
                name=str(entry.get("name", "")).strip(),
                client_version=int(entry.get("client_version", 0) or 0),
                assets_dir=str(entry.get("assets_dir", "")).strip(),
                preferred_kind=str(entry.get("preferred_kind", "auto") or "auto"),
                profile_id=str(entry.get("profile_id", "")).strip() or None,
                existing_ids=used_ids,
            )
        except Exception:
            continue
        if candidate.profile_id in used_ids:
            candidate = create_client_profile(
                name=candidate.name,
                client_version=candidate.client_version,
                assets_dir=candidate.assets_dir,
                preferred_kind=candidate.preferred_kind,
                existing_ids=used_ids,
            )
        profiles.append(candidate)
        used_ids.add(candidate.profile_id)

    return profiles


def dump_client_profiles(profiles: list[ClientProfile]) -> str:
    """Serialize profiles into compact JSON for QSettings."""
    normalized: list[ClientProfile] = []
    used_ids: set[str] = set()
    for profile in profiles:
        try:
            entry = create_client_profile(
                name=profile.name,
                client_version=profile.client_version,
                assets_dir=profile.assets_dir,
                preferred_kind=profile.preferred_kind,
                profile_id=profile.profile_id,
                existing_ids=used_ids,
            )
        except Exception:
            continue
        if entry.profile_id in used_ids:
            entry = create_client_profile(
                name=entry.name,
                client_version=entry.client_version,
                assets_dir=entry.assets_dir,
                preferred_kind=entry.preferred_kind,
                existing_ids=used_ids,
            )
        normalized.append(entry)
        used_ids.add(entry.profile_id)

    data = [asdict(item) for item in normalized]
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def resolve_active_client_profile(
    *,
    profiles: list[ClientProfile],
    active_profile_id: str,
    client_version: int | None = None,
) -> ClientProfile | None:
    """Resolve currently active profile using id and optional client version hint."""
    requested_id = normalize_profile_id(active_profile_id) if active_profile_id else ""
    if requested_id:
        for profile in profiles:
            if profile.profile_id == requested_id:
                return profile

    if client_version is not None and int(client_version) > 0:
        target = int(client_version)
        for profile in profiles:
            if int(profile.client_version) == target:
                return profile

    if profiles:
        return profiles[0]
    return None
