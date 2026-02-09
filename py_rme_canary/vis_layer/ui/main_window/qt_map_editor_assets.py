from __future__ import annotations

import contextlib
import json
import logging
import os
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox, QProgressDialog

from py_rme_canary.core.assets.appearances_dat import AppearancesDatError, load_appearances_dat
from py_rme_canary.core.assets.asset_profile import AssetProfileError, detect_asset_profile
from py_rme_canary.core.assets.legacy_dat_spr import LegacySpriteError
from py_rme_canary.core.assets.loader import load_assets_from_profile
from py_rme_canary.core.assets.sprite_appearances import SpriteAppearancesError
from py_rme_canary.core.config.client_profiles import ClientProfile
from py_rme_canary.core.config.configuration_manager import ConfigurationManager
from py_rme_canary.core.config.project import MapMetadata, find_project_for_otbm
from py_rme_canary.core.config.user_settings import get_user_settings
from py_rme_canary.core.database.id_mapper import IdMapper
from py_rme_canary.core.database.items_otb import ItemsOTB, ItemsOTBError
from py_rme_canary.core.database.items_xml import ItemsXML
from py_rme_canary.core.memory_guard import MemoryGuardError
from py_rme_canary.vis_layer.ui.dialogs.client_data_loader_dialog import ClientDataLoadConfig, ClientDataLoaderDialog

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


logger = logging.getLogger(__name__)


class QtMapEditorAssetsMixin:
    # ---------- assets (legacy sprite sheets) ----------

    def _preferred_asset_kind(self: QtMapEditor) -> str | None:
        cv = int(self.client_version or 0)
        if cv >= 1100:
            return "modern"
        if cv > 0:
            return "legacy"
        return None

    @staticmethod
    def _workspace_root_for_definitions() -> Path:
        cwd = Path.cwd().resolve()
        package_root = Path(__file__).resolve().parents[3]
        repo_root = Path(__file__).resolve().parents[4]
        candidates = [cwd, repo_root, package_root]
        for candidate in candidates:
            if (candidate / "py_rme_canary" / "data").exists() or (candidate / "data").exists():
                return candidate
        return cwd

    def _set_id_mapper(self: QtMapEditor, mapper: IdMapper | None) -> None:
        self.id_mapper = mapper
        with contextlib.suppress(Exception):
            from py_rme_canary.logic_layer.asset_manager import AssetManager

            AssetManager.instance().set_id_mapper(mapper)
        with contextlib.suppress(Exception):
            self._build_item_hash_index()

    def _client_id_for_server_id(self: QtMapEditor, server_id: int) -> int | None:
        mapper = getattr(self, "id_mapper", None)
        if mapper is None:
            return None
        with contextlib.suppress(Exception):
            mapped = mapper.get_client_id(int(server_id))
            if mapped is None:
                return None
            return int(mapped)
        return None

    def _reload_item_definitions_for_current_context(self: QtMapEditor, *, source: str) -> list[str]:
        md = MapMetadata(
            engine=str(self.engine or "unknown"),
            client_version=int(self.client_version or 0),
            otbm_version=int(getattr(self.map.header, "otbm_version", 0)) if getattr(self, "map", None) else 0,
            source=str(source),
        )
        cfg = ConfigurationManager.from_sniff(md, workspace_root=self._workspace_root_for_definitions())
        _items_db, id_mapper, warnings = self._load_items_definitions_for_config(cfg)
        self._set_id_mapper(id_mapper)
        if cfg.definitions.items_otb is None and cfg.definitions.items_xml is None:
            warnings.append(
                "items_definitions_missing: could not locate items.otb/items.xml for "
                f"engine={md.engine} client_version={int(md.client_version)}"
            )
        return warnings

    @staticmethod
    def _normalize_optional_path(raw_path: str) -> Path | None:
        normalized = str(raw_path or "").strip()
        if not normalized:
            return None
        return Path(normalized).expanduser().resolve()

    def _refresh_after_asset_data_load(self: QtMapEditor) -> None:
        with contextlib.suppress(Exception):
            self.palettes.refresh_primary_list()
        with contextlib.suppress(Exception):
            self.canvas.update()
        with contextlib.suppress(Exception):
            self._update_sprite_preview()

    def _open_client_data_loader(self: QtMapEditor) -> None:
        dialog = ClientDataLoaderDialog(
            self,
            default_assets_path=str(getattr(self, "assets_selection_path", "") or ""),
            default_client_version=int(getattr(self, "client_version", 0) or 0),
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        config = dialog.config()
        self._load_client_data_stack(config, source="interactive_loader")

    def _load_client_data_stack(self: QtMapEditor, config: ClientDataLoadConfig, *, source: str) -> None:
        progress = QProgressDialog("Preparing client data load...", "Cancel", 0, 5, self)
        progress.setWindowTitle("Load Client Data")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setAutoClose(True)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        def advance(step: int, message: str) -> None:
            progress.setLabelText(message)
            progress.setValue(int(step))
            QApplication.processEvents()
            if progress.wasCanceled():
                raise RuntimeError("Client data load canceled by user.")

        try:
            if int(config.client_version_hint) > 0:
                self.client_version = int(config.client_version_hint)
                self.engine = ConfigurationManager.infer_engine_from_client_version(int(config.client_version_hint))

            self.assets_selection_path = str(config.assets_path)
            user_settings = get_user_settings()
            user_settings.set_client_assets_folder(str(config.assets_path))
            if int(config.client_version_hint) > 0:
                user_settings.set_default_client_version(int(config.client_version_hint))

            prefer_kind = str(config.prefer_kind or "auto").strip().lower()
            prefer = None if prefer_kind == "auto" else prefer_kind

            advance(1, "Detecting client asset profile...")
            profile = detect_asset_profile(str(config.assets_path), prefer_kind=prefer)

            advance(2, "Loading sprites and appearance metadata...")
            loaded_assets = self._apply_asset_profile(profile)
            if loaded_assets is None or self.sprite_assets is None:
                raise RuntimeError("Asset profile loading did not initialize sprite assets.")

            advance(3, "Loading item definitions (items.otb / items.xml)...")
            explicit_otb = self._normalize_optional_path(config.items_otb_path)
            explicit_xml = self._normalize_optional_path(config.items_xml_path)
            if explicit_otb is not None or explicit_xml is not None:
                id_mapper, warnings, explicit_counts = self._load_item_definitions_from_explicit_paths(
                    items_otb_path=explicit_otb,
                    items_xml_path=explicit_xml,
                )
                self._set_id_mapper(id_mapper)
            else:
                warnings = self._reload_item_definitions_for_current_context(source=source)
                explicit_counts = {}

            advance(4, "Refreshing editor UI and grid previews...")
            self._refresh_after_asset_data_load()

            advance(5, "Finalizing load summary...")
            mapping_count = len(getattr(getattr(self, "id_mapper", None), "server_to_client", {}) or {})
            summary = self._build_client_data_load_summary(
                profile=profile,
                warnings=warnings,
                mapping_count=mapping_count,
                explicit_counts=explicit_counts,
                source=source,
            )
            self._update_status_capabilities(prefix="Client data stack loaded")
            if bool(config.show_summary):
                QMessageBox.information(self, "Load Client Data", summary)

        except Exception as exc:
            logger.exception("Client data stack load failed")
            QMessageBox.critical(self, "Load Client Data", str(exc))
        finally:
            progress.close()

    def _build_client_data_load_summary(
        self: QtMapEditor,
        *,
        profile,
        warnings: list[str],
        mapping_count: int,
        explicit_counts: dict[str, int],
        source: str,
    ) -> str:
        profile_kind = str(getattr(profile, "kind", "unknown"))
        profile_root = str(getattr(profile, "assets_dir", None) or getattr(profile, "root", ""))
        sprites_info = ""
        if hasattr(self, "sprite_assets") and self.sprite_assets is not None:
            sprite_count = int(getattr(self.sprite_assets, "sprite_count", 0) or 0)
            if sprite_count > 0:
                sprites_info = f"\nSprite count: {sprite_count}"
        appearance_state = "loaded" if self.appearance_assets is not None else "not loaded"
        item_count = int(explicit_counts.get("items_xml_count", 0))
        details = [
            f"Source: {source}",
            f"Profile: {profile_kind}",
            f"Assets root: {profile_root}",
            f"Appearances: {appearance_state}",
            f"ID mappings: {int(mapping_count)}",
        ]
        if item_count > 0:
            details.append(f"items.xml entries: {item_count}")
        if sprites_info:
            details.append(sprites_info.strip())
        if warnings:
            details.append(f"Warnings: {len(warnings)}")
            details.extend([f"- {msg}" for msg in warnings[:6]])
        else:
            details.append("Warnings: 0")
        return "\n".join(details)

    def _load_item_definitions_from_explicit_paths(
        self: QtMapEditor,
        *,
        items_otb_path: Path | None,
        items_xml_path: Path | None,
    ) -> tuple[IdMapper | None, list[str], dict[str, int]]:
        warnings: list[str] = []
        counts: dict[str, int] = {}

        items_db: ItemsXML | None = None
        if items_xml_path is not None:
            try:
                items_db = ItemsXML.load(items_xml_path, strict_mapping=False)
                counts["items_xml_count"] = len(getattr(items_db, "items_by_server_id", {}) or {})
            except Exception as exc:
                warnings.append(f"items_xml_error: {exc}")

        id_mapper: IdMapper | None = None
        if items_otb_path is not None:
            try:
                items_otb = ItemsOTB.load(items_otb_path)
                id_mapper = IdMapper.from_items_otb(items_otb)
                counts["items_otb_count"] = len(getattr(id_mapper, "server_to_client", {}) or {})
            except Exception as exc:
                warnings.append(f"items_otb_error: {exc}")

        if id_mapper is None and items_db is not None:
            id_mapper = IdMapper.from_items_xml(items_db)
            counts["items_otb_count"] = len(getattr(id_mapper, "server_to_client", {}) or {})
            warnings.append("items_otb_fallback: using explicit items.xml mapping fallback")

        return id_mapper, warnings, counts

    def _choose_assets_dir(self: QtMapEditor) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Tibia client folder or assets folder")
        if not path:
            return
        self._set_assets_dir(path)

    def _manage_client_profiles(self: QtMapEditor) -> None:
        from py_rme_canary.vis_layer.ui.dialogs.client_profiles_dialog import ClientProfilesDialog

        user_settings = get_user_settings()
        profiles = user_settings.get_client_profiles()
        active_id = user_settings.get_active_client_profile_id()

        dialog = ClientProfilesDialog(parent=self, profiles=profiles, active_profile_id=active_id)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        updated_profiles = dialog.result_profiles()
        updated_active_id = dialog.result_active_profile_id()

        user_settings.set_client_profiles(updated_profiles)
        user_settings.set_active_client_profile_id(updated_active_id)

        selected_profile = user_settings.get_active_client_profile(client_version=int(self.client_version or 0))
        if selected_profile is not None:
            try:
                self._apply_client_profile(selected_profile, persist_active=False)
            except Exception as exc:
                QMessageBox.critical(self, "Client Profiles", str(exc))
                logger.exception("Failed to load selected client profile")
        else:
            self.status.showMessage("Client profiles updated.")

    def _apply_client_profile(self: QtMapEditor, profile: ClientProfile, *, persist_active: bool = True) -> None:
        assets_dir = str(profile.assets_dir or "").strip()
        if not assets_dir:
            raise ValueError("Client profile assets directory cannot be empty.")
        if not os.path.exists(assets_dir):
            raise ValueError(f"Assets directory does not exist: {assets_dir}")

        preferred_kind = str(profile.preferred_kind or "auto").strip().lower()
        if preferred_kind not in {"auto", "modern", "legacy"}:
            preferred_kind = "auto"

        profile_version = int(profile.client_version or 0)
        if profile_version > 0:
            self.client_version = int(profile_version)
            self.engine = ConfigurationManager.infer_engine_from_client_version(int(profile_version))

        self.assets_selection_path = assets_dir
        resolved_profile = detect_asset_profile(
            assets_dir,
            prefer_kind=None if preferred_kind == "auto" else preferred_kind,
        )
        self._apply_asset_profile(resolved_profile)
        warnings = self._reload_item_definitions_for_current_context(source=f"profile:{profile.profile_id}")
        if warnings:
            self.status.showMessage(warnings[0])
            logger.warning(" | ".join(warnings))
        self._build_sprite_hash_database()
        self._refresh_after_asset_data_load()

        user_settings = get_user_settings()
        user_settings.set_client_assets_folder(assets_dir)
        if profile_version > 0:
            user_settings.set_default_client_version(profile_version)
        if persist_active:
            user_settings.set_active_client_profile_id(profile.profile_id)

        self._update_status_capabilities(prefix=f"Client profile loaded: {profile.name}")

    def _set_assets_dir(self: QtMapEditor, assets_dir: str) -> None:
        try:
            self.assets_selection_path = str(assets_dir)
            logger.info("Assets directory set: %s", assets_dir)
            profile = detect_asset_profile(assets_dir, prefer_kind=self._preferred_asset_kind())
        except AssetProfileError as e:
            QMessageBox.critical(self, "Assets", str(e))
            logger.exception("Failed to detect assets for path %s", assets_dir)
            return
        self._apply_asset_profile(profile)
        warnings = self._reload_item_definitions_for_current_context(source="manual_assets_dir")
        if warnings:
            self.status.showMessage(warnings[0])
            logger.warning(" | ".join(warnings))
        self._build_sprite_hash_database()
        self._refresh_after_asset_data_load()

    def _apply_asset_profile(self: QtMapEditor, profile) -> None:
        user_settings = get_user_settings()
        if str(getattr(profile, "kind", "")).lower() == "modern" and not user_settings.get_auto_load_appearances():
            with contextlib.suppress(Exception):
                profile = replace(profile, appearances_path=None)
        self.asset_profile = profile
        try:
            logger.info("Applying asset profile: %s", profile.describe())
        except Exception:
            logger.info("Applying asset profile")
        try:
            loaded = load_assets_from_profile(profile, memory_guard=self._memory_guard)
        except (AssetProfileError, SpriteAppearancesError, LegacySpriteError) as exc:
            QMessageBox.critical(self, "Assets", str(exc))
            logger.exception("Failed to load assets")
            return

        self.assets_dir = str(profile.assets_dir or profile.root)
        self.sprite_assets = loaded.sprite_assets
        self.appearance_assets = loaded.appearance_assets
        self._sprite_cache.clear()
        self._sprite_render_temporarily_disabled = False
        self._sprite_render_disabled_reason = None

        # Build sprite hash database for cross-version clipboard
        self._build_sprite_hash_database()

        prefix_parts: list[str] = []
        if loaded.sheet_count is not None:
            prefix_parts.append(f"sheets: {loaded.sheet_count}")
        if loaded.sprite_count is not None:
            prefix_parts.append(f"sprites: {loaded.sprite_count}")
        prefix_suffix = f" ({', '.join(prefix_parts)})" if prefix_parts else ""
        self._update_status_capabilities(prefix=f"Assets loaded: {self.assets_dir}{prefix_suffix}")

        if loaded.appearance_error:
            self.status.showMessage(f"Appearances load failed: {loaded.appearance_error}")
            logger.warning("Appearances load failed: %s", loaded.appearance_error)

        if loaded.fallback_notice:
            self.status.showMessage(str(loaded.fallback_notice))
            logger.warning(str(loaded.fallback_notice))

        self._refresh_after_asset_data_load()
        return loaded

    def _apply_detected_context(self: QtMapEditor, metadata: dict) -> None:
        prev_engine = str(self.engine)
        self.engine = str(metadata.get("engine") or "unknown")
        self.client_version = int(metadata.get("client_version") or 0)
        if self.engine != prev_engine:
            # Engine switch should never explode any downstream rendering.
            self._sprite_cache.clear()
            self._sprite_render_temporarily_disabled = False
            self._sprite_render_disabled_reason = None
        self._maybe_reselect_assets_for_metadata()
        if self.id_mapper is None:
            warnings = self._reload_item_definitions_for_current_context(source="detected_context")
            if warnings:
                self.status.showMessage(warnings[0])
                logger.warning(" | ".join(warnings))

    def _apply_preferences_for_new_map(self: QtMapEditor) -> None:
        user_settings = get_user_settings()
        active_profile = user_settings.get_active_client_profile()
        preferred_cv = int(getattr(active_profile, "client_version", 0) or 0)
        if preferred_cv <= 0:
            preferred_cv = int(user_settings.get_default_client_version() or 0)
        if preferred_cv > 0:
            self.client_version = int(preferred_cv)
            self.engine = ConfigurationManager.infer_engine_from_client_version(int(preferred_cv))
        else:
            self.client_version = 0
            self.engine = "unknown"

        loaded_from_profile = False
        if active_profile is not None:
            profile_assets = str(getattr(active_profile, "assets_dir", "") or "").strip()
            if profile_assets and os.path.exists(profile_assets):
                try:
                    self._apply_client_profile(active_profile, persist_active=False)
                    loaded_from_profile = True
                except Exception:
                    logger.exception("Failed to auto-load active client profile")

        if not loaded_from_profile:
            assets_folder = str(user_settings.get_client_assets_folder() or "").strip()
            if assets_folder and os.path.exists(assets_folder):
                self._set_assets_dir(assets_folder)

        warnings = self._reload_item_definitions_for_current_context(source="preferences")
        if warnings:
            self.status.showMessage(warnings[0])
            logger.warning(" | ".join(warnings))

        self._update_status_capabilities(prefix="New map initialized from preferences")

    @staticmethod
    def _load_items_definitions_for_config(
        cfg: ConfigurationManager,
    ) -> tuple[ItemsXML | None, IdMapper | None, list[str]]:
        warnings: list[str] = []

        items_db: ItemsXML | None = None
        if cfg.definitions.items_xml is not None:
            try:
                items_db = ItemsXML.load(cfg.definitions.items_xml, strict_mapping=False)
            except Exception as e:
                warnings.append(f"items_xml_error: {e}")

        id_mapper: IdMapper | None = None
        if cfg.definitions.items_otb is not None:
            try:
                items_otb = ItemsOTB.load(cfg.definitions.items_otb)
                id_mapper = IdMapper.from_items_otb(items_otb)
            except ItemsOTBError as e:
                warnings.append(f"items_otb_error: {e}")
            except Exception as e:
                warnings.append(f"items_otb_error: {e}")

        if id_mapper is None and items_db is not None:
            id_mapper = IdMapper.from_items_xml(items_db)
            warnings.append("items_otb_fallback: using items.xml mapping fallback")

        return items_db, id_mapper, warnings

    def _maybe_reselect_assets_for_metadata(self: QtMapEditor) -> None:
        prefer = self._preferred_asset_kind()
        if prefer is None:
            return
        profile = getattr(self, "asset_profile", None)
        selection = getattr(self, "assets_selection_path", None)
        if profile is None or not selection:
            return
        if str(getattr(profile, "kind", "")).lower() == prefer and not getattr(profile, "is_ambiguous", False):
            return
        try:
            new_profile = detect_asset_profile(selection, prefer_kind=prefer)
        except Exception:
            return
        if str(getattr(new_profile, "kind", "")).lower() != str(getattr(profile, "kind", "")).lower():
            self._apply_asset_profile(new_profile)

    def _disable_sprite_render_temporarily(self: QtMapEditor, *, reason: str) -> None:
        # Sprites are derived + recreatable. Never crash the editor because of them.
        self._sprite_render_temporarily_disabled = True
        self._sprite_render_disabled_reason = str(reason)
        with contextlib.suppress(Exception):
            self._sprite_cache.clear()

        # One clear warning; after that keep it in the status bar.
        msg = (
            "Sprite rendering was temporarily disabled due to memory pressure/driver failure. "
            "You can keep editing (sprites may be hidden)."
        )
        with contextlib.suppress(Exception):
            self.status.showMessage(f"{msg} | reason={reason}")

        if not bool(getattr(self, "_sprite_render_emergency_warned", False)):
            self._sprite_render_emergency_warned = True
            with contextlib.suppress(Exception):
                QMessageBox.warning(self, "Sprites disabled", f"{msg}\n\nReason: {reason}")

    def _sprite_render_enabled(self: QtMapEditor) -> bool:
        if bool(getattr(self, "_sprite_render_temporarily_disabled", False)):
            return False
        return self.sprite_assets is not None

    def _update_status_capabilities(self: QtMapEditor, *, prefix: str = "") -> None:
        assets = "ON" if self.sprite_assets is not None else "OFF"
        mapping = "ON" if self.id_mapper is not None else "OFF"
        appearances = "ON" if self.appearance_assets is not None else "OFF"
        sprite = "ON" if self._sprite_render_enabled() else "OFF"
        profile = getattr(self, "asset_profile", None)
        profile_kind = str(getattr(profile, "kind", "none"))
        engine = str(self.engine or "unknown")
        cv = int(self.client_version or 0)
        otbm_version = 0
        try:
            if getattr(self, "map", None) is not None:
                otbm_version = int(getattr(self.map.header, "otbm_version", 0))
        except Exception:
            otbm_version = 0
        cap = (
            f"engine={engine} client={cv} otbm={otbm_version} | profile={profile_kind} assets={assets} "
            f"appearances={appearances} mapping={mapping} sprite={sprite}"
        )
        msg = f"{prefix} | {cap}" if prefix else cap
        self.status.showMessage(msg)

    def _load_appearances_dat(self: QtMapEditor) -> None:
        profile = getattr(self, "asset_profile", None)
        if profile is None or str(getattr(profile, "kind", "")).lower() != "modern":
            QMessageBox.information(self, "Appearances", "Modern assets are required to load appearances.dat.")
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select appearances.dat",
            str(getattr(profile, "assets_dir", profile.root)),
            "Appearances (appearances.dat);;All files (*.*)",
        )
        if not path:
            return

        try:
            self.appearance_assets = load_appearances_dat(path)
        except AppearancesDatError as exc:
            QMessageBox.critical(self, "Appearances", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Appearances", str(exc))
            return

        with contextlib.suppress(Exception):
            self.asset_profile = replace(profile, appearances_path=Path(path))

        self._update_status_capabilities(prefix=f"Appearances loaded: {path}")

    def _unload_appearances_dat(self: QtMapEditor) -> None:
        self.appearance_assets = None
        profile = getattr(self, "asset_profile", None)
        if profile is not None and str(getattr(profile, "kind", "")).lower() == "modern":
            with contextlib.suppress(Exception):
                self.asset_profile = replace(profile, appearances_path=None)
        self._update_status_capabilities(prefix="Appearances unloaded")

    def _resolve_sprite_id_from_client_id(self: QtMapEditor, client_id: int) -> int | None:
        if self.appearance_assets is None:
            return int(client_id)
        profile = getattr(self, "asset_profile", None)
        if str(getattr(profile, "kind", "")).lower() == "legacy":
            return int(client_id)
        cv = int(self.client_version or 0)
        if cv > 0 and cv < 1100:
            return int(client_id)
        time_ms = None
        if hasattr(self, "animation_time_ms") and getattr(self, "show_preview", False):
            time_ms = int(self.animation_time_ms())
        sprite_id = self.appearance_assets.get_sprite_id(
            int(client_id),
            kind="object",
            time_ms=time_ms,
            seed=int(client_id),
        )
        if sprite_id is None:
            return int(client_id)
        return int(sprite_id)

    def _candidate_sprite_ids_for_server_id(self: QtMapEditor, server_id: int) -> list[int]:
        candidates: list[int] = []
        sid = int(server_id)

        if self.id_mapper is not None:
            with contextlib.suppress(Exception):
                cid = self.id_mapper.get_client_id(sid)
                if cid is not None and int(cid) > 0:
                    resolved = self._resolve_sprite_id_from_client_id(int(cid))
                    if resolved is not None and int(resolved) > 0:
                        candidates.append(int(resolved))
                    candidates.append(int(cid))

        with contextlib.suppress(Exception):
            resolved_sid = self._resolve_sprite_id_from_client_id(sid)
            if resolved_sid is not None and int(resolved_sid) > 0:
                candidates.append(int(resolved_sid))

        candidates.append(sid)

        unique: list[int] = []
        seen: set[int] = set()
        for value in candidates:
            iv = int(value)
            if iv <= 0 or iv in seen:
                continue
            seen.add(iv)
            unique.append(iv)
        return unique

    def _maybe_write_default_project_json(self: QtMapEditor, *, opened_otbm_path: str, cfg) -> None:
        # Legacy-friendly behavior: if user opens a bare .otbm without any wrapper,
        # write a minimal map_project.json so subsequent opens are deterministic.
        try:
            p = os.path.abspath(opened_otbm_path)
            proj_path = find_project_for_otbm(p)
            if proj_path is not None:
                return
            map_dir = os.path.dirname(p)
            out_path = os.path.join(map_dir, "map_project.json")
            if os.path.exists(out_path):
                return

            def rel_or_abs(path_value):
                if path_value is None:
                    return None
                try:
                    return os.path.relpath(str(path_value), map_dir)
                except Exception:
                    return str(path_value)

            doc = {
                "project_name": "",
                "metadata": {
                    "engine": str(
                        getattr(cfg, "metadata", None).engine if getattr(cfg, "metadata", None) else "unknown"
                    ),
                    "client_version": int(
                        getattr(cfg, "metadata", None).client_version if getattr(cfg, "metadata", None) else 0
                    ),
                },
                "map_file": os.path.basename(p),
                "definitions": {
                    "items_otb": rel_or_abs(
                        getattr(cfg, "definitions", None).items_otb if getattr(cfg, "definitions", None) else None
                    ),
                    "items_xml": rel_or_abs(
                        getattr(cfg, "definitions", None).items_xml if getattr(cfg, "definitions", None) else None
                    ),
                },
            }
            # Drop nulls for cleanliness.
            doc["definitions"] = {k: v for k, v in doc["definitions"].items() if v}
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=2)
        except Exception:
            # Never crash UI for project autogen.
            return

    def _sprite_pixmap_for_server_id(self: QtMapEditor, server_id: int, *, tile_px: int) -> QPixmap | None:
        if not self._sprite_render_enabled():
            return None
        if self.sprite_assets is None:
            return None
        for sprite_id in self._candidate_sprite_ids_for_server_id(int(server_id)):
            key = (int(sprite_id), int(tile_px))
            cached = self._sprite_cache.get(key)
            if cached is not None:
                with contextlib.suppress(Exception):
                    self._sprite_cache.move_to_end(key)
                return cached
            try:
                w, h, bgra = self.sprite_assets.get_sprite_rgba(int(sprite_id))
                img = QImage(bgra, int(w), int(h), int(w) * 4, QImage.Format.Format_ARGB32).copy()
                pm = QPixmap.fromImage(img)
                if pm.isNull():
                    self._disable_sprite_render_temporarily(reason="QPixmap.fromImage returned null")
                    return None
                if int(tile_px) > 0 and (pm.width() != int(tile_px) or pm.height() != int(tile_px)):
                    pm2 = pm.scaled(
                        int(tile_px),
                        int(tile_px),
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.FastTransformation,
                    )
                    if pm2.isNull():
                        self._disable_sprite_render_temporarily(reason="QPixmap.scaled returned null")
                        return None
                    pm = pm2
                try:
                    self._sprite_cache[key] = pm
                    self._sprite_cache.move_to_end(key)
                except Exception:
                    return pm

                try:
                    msg = self._memory_guard.check_cache_entries(
                        kind="qt_pixmap_cache",
                        entries=len(self._sprite_cache),
                        stage="qt_sprite_cache",
                    )
                    if msg is not None:
                        self.status.showMessage(str(msg))
                except MemoryGuardError:
                    hard = int(self._memory_guard.config.hard_qt_pixmap_cache_entries)
                    evict_to = int(self._memory_guard.config.evict_to_qt_pixmap_cache_entries)
                    target = min(max(0, evict_to), max(0, hard - 1)) if hard > 0 else 0
                    try:
                        while len(self._sprite_cache) > target and self._sprite_cache:
                            self._sprite_cache.popitem(last=False)
                    except Exception:
                        self._sprite_cache.clear()
                return pm
            except MemoryError:
                self._disable_sprite_render_temporarily(reason="MemoryError while building QPixmap")
                return None
            except SpriteAppearancesError:
                continue
            except Exception:
                continue
        return None

    def _sprite_bgra_for_server_id(self: QtMapEditor, server_id: int) -> tuple[int, int, int, bytes] | None:
        if not self._sprite_render_enabled():
            return None
        if self.sprite_assets is None:
            return None
        for sprite_id in self._candidate_sprite_ids_for_server_id(int(server_id)):
            try:
                w, h, bgra = self.sprite_assets.get_sprite_rgba(int(sprite_id))
                return (int(sprite_id), int(w), int(h), bgra)
            except MemoryError:
                self._disable_sprite_render_temporarily(reason="MemoryError while building sprite bytes")
                return None
            except SpriteAppearancesError:
                continue
            except Exception:
                continue
        return None

    def _build_item_hash_index(self: QtMapEditor) -> None:
        """Build hash indexes keyed by ServerID for cross-instance clipboard."""
        self._item_hash_to_server_ids: dict[int, list[int]] = {}
        self._server_id_to_item_hash: dict[int, int] = {}

        matcher = getattr(self, "sprite_matcher", None)
        if matcher is None or self.id_mapper is None:
            return

        server_to_client = dict(getattr(self.id_mapper, "server_to_client", {}) or {})
        indexed = 0
        for server_id, client_id in server_to_client.items():
            try:
                sprite_id = self._resolve_sprite_id_from_client_id(int(client_id))
            except Exception:
                continue
            if sprite_id is None or int(sprite_id) <= 0:
                continue

            sprite_hash = matcher.get_hash(int(sprite_id))
            if sprite_hash is None:
                # Lazy add hash for sprites outside initial preload window.
                bgra_data = self._sprite_bgra_for_server_id(int(server_id))
                if bgra_data is None:
                    continue
                sprite_id, width, height, bgra = bgra_data
                try:
                    matcher.add_sprite(int(sprite_id), bytes(bgra), int(width), int(height))
                except Exception:
                    continue
                sprite_hash = matcher.get_hash(int(sprite_id))
            if sprite_hash is None:
                continue

            h = int(sprite_hash)
            sid = int(server_id)
            self._server_id_to_item_hash[sid] = h
            bucket = self._item_hash_to_server_ids.setdefault(h, [])
            if sid not in bucket:
                bucket.append(sid)
            indexed += 1

        for ids in self._item_hash_to_server_ids.values():
            ids.sort()

        logger.info(
            "Built item hash index: %d items across %d unique hashes",
            indexed,
            len(self._item_hash_to_server_ids),
        )

    def _sprite_hash_for_server_id(self: QtMapEditor, server_id: int) -> int | None:
        """Return sprite hash for a ServerID using current assets profile."""
        sid = int(server_id)
        cached = getattr(self, "_server_id_to_item_hash", {}).get(sid)
        if cached is not None:
            return int(cached)

        matcher = getattr(self, "sprite_matcher", None)
        if matcher is None:
            return None

        bgra_data = self._sprite_bgra_for_server_id(sid)
        if bgra_data is None:
            return None
        sprite_id, width, height, bgra = bgra_data
        try:
            matcher.add_sprite(int(sprite_id), bytes(bgra), int(width), int(height))
        except Exception:
            return None

        sprite_hash = matcher.get_hash(int(sprite_id))
        if sprite_hash is None:
            return None

        h = int(sprite_hash)
        self._server_id_to_item_hash[sid] = h
        bucket = self._item_hash_to_server_ids.setdefault(h, [])
        if sid not in bucket:
            bucket.append(sid)
            bucket.sort()
        return h

    def _resolve_server_id_from_sprite_hash(
        self: QtMapEditor,
        sprite_hash: int,
        original_id: int | None = None,
        _name: str | None = None,
    ) -> int | None:
        """Resolve local ServerID candidate from incoming sprite hash."""
        bucket = getattr(self, "_item_hash_to_server_ids", {}).get(int(sprite_hash), [])
        if not bucket:
            return None
        if original_id is not None and int(original_id) in bucket:
            return int(original_id)
        return int(bucket[0])

    def _update_sprite_preview(self: QtMapEditor) -> None:
        if self.sprite_assets is None:
            self.sprite_preview.setText("No assets loaded")
            self.sprite_preview.setPixmap(QPixmap())
            return

        sid = int(self.sprite_id_spin.value())
        if sid <= 0:
            self.sprite_preview.setText("Enter a spriteId")
            self.sprite_preview.setPixmap(QPixmap())
            return

        try:
            w, h, bgra = self.sprite_assets.get_sprite_rgba(sid)
            # QImage.Format_ARGB32 expects BGRA byte order on little-endian.
            img = QImage(bgra, int(w), int(h), int(w) * 4, QImage.Format.Format_ARGB32).copy()
            pm = QPixmap.fromImage(img)
            # Scale up for visibility.
            pm = pm.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
            self.sprite_preview.setPixmap(pm)
            self.sprite_preview.setText("")
        except Exception as e:
            self.sprite_preview.setText(str(e))
            self.sprite_preview.setPixmap(QPixmap())

    def _build_sprite_hash_database(self: QtMapEditor) -> None:
        """Build sprite hash database for cross-version clipboard matching."""
        try:
            from py_rme_canary.logic_layer.cross_version.sprite_hash import SpriteHashMatcher

            # Initialize sprite matcher
            if not hasattr(self, "sprite_matcher") or self.sprite_matcher is None:
                self.sprite_matcher = SpriteHashMatcher()
            else:
                self.sprite_matcher.clear()

            # Skip if no assets loaded
            if self.sprite_assets is None or self.id_mapper is None:
                logger.debug("Skipping sprite hash database build - no assets loaded")
                self._item_hash_to_server_ids = {}
                self._server_id_to_item_hash = {}
                return

            # Get sprite count
            sprite_count = 0
            with contextlib.suppress(Exception):
                sprite_count = getattr(self.sprite_assets, "sprite_count", 0) or 0

            if sprite_count <= 0:
                logger.debug("No sprites to hash")
                self._item_hash_to_server_ids = {}
                self._server_id_to_item_hash = {}
                return

            # Build hash for each sprite (limit to avoid performance issues)
            max_sprites = min(int(sprite_count), 50000)
            hashed_count = 0

            for sprite_id in range(1, max_sprites + 1):
                try:
                    w, h, bgra = self.sprite_assets.get_sprite_rgba(int(sprite_id))
                    if w > 0 and h > 0 and bgra:
                        self.sprite_matcher.add_sprite(int(sprite_id), bytes(bgra), int(w), int(h))
                        hashed_count += 1
                except Exception:
                    # Sprite doesn't exist or failed to load, skip
                    continue

            logger.info(f"Built sprite hash database: {hashed_count} sprites hashed from {max_sprites} total")
            self._build_item_hash_index()

        except ImportError:
            logger.warning("CrossVersionClipboard not available")
            self.sprite_matcher = None
            self._item_hash_to_server_ids = {}
            self._server_id_to_item_hash = {}
        except Exception as e:
            logger.exception(f"Failed to build sprite hash database: {e}")
            self.sprite_matcher = None
            self._item_hash_to_server_ids = {}
            self._server_id_to_item_hash = {}
