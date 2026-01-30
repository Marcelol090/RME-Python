from __future__ import annotations

import json
import logging
import os
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from py_rme_canary.core.assets.appearances_dat import AppearancesDatError, load_appearances_dat
from py_rme_canary.core.assets.asset_profile import AssetProfileError, detect_asset_profile
from py_rme_canary.core.assets.legacy_dat_spr import LegacySpriteError
from py_rme_canary.core.assets.loader import load_assets_from_profile
from py_rme_canary.core.assets.sprite_appearances import SpriteAppearancesError
from py_rme_canary.core.config.configuration_manager import ConfigurationManager
from py_rme_canary.core.config.project import MapMetadata, find_project_for_otbm
from py_rme_canary.core.config.user_settings import get_user_settings
from py_rme_canary.core.database.id_mapper import IdMapper
from py_rme_canary.core.database.items_otb import ItemsOTB, ItemsOTBError
from py_rme_canary.core.database.items_xml import ItemsXML
from py_rme_canary.core.memory_guard import MemoryGuardError

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

    def _choose_assets_dir(self: QtMapEditor) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Tibia client folder or assets folder")
        if not path:
            return
        try:
            self.assets_selection_path = str(path)
            logger.info("Assets directory selected: %s", path)
            profile = detect_asset_profile(path, prefer_kind=self._preferred_asset_kind())
            self._apply_asset_profile(profile)
        except (AssetProfileError, SpriteAppearancesError) as e:
            QMessageBox.critical(self, "Assets", str(e))
            logger.exception("Failed to detect assets for path %s", path)

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

    def _apply_asset_profile(self: QtMapEditor, profile) -> None:
        user_settings = get_user_settings()
        if str(getattr(profile, "kind", "")).lower() == "modern" and not user_settings.get_auto_load_appearances():
            try:
                profile = replace(profile, appearances_path=None)
            except Exception:
                pass
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

        self._update_sprite_preview()

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

    def _apply_preferences_for_new_map(self: QtMapEditor) -> None:
        user_settings = get_user_settings()
        preferred_cv = int(user_settings.get_default_client_version() or 0)
        if preferred_cv > 0:
            self.client_version = int(preferred_cv)
            self.engine = ConfigurationManager.infer_engine_from_client_version(int(preferred_cv))
        else:
            self.client_version = 0
            self.engine = "unknown"

        md = MapMetadata(
            engine=str(self.engine or "unknown"),
            client_version=int(self.client_version or 0),
            otbm_version=int(getattr(self.map.header, "otbm_version", 0)) if self.map else 0,
            source="preferences",
        )
        cfg = ConfigurationManager.from_sniff(md, workspace_root=Path.cwd())
        _items_db, id_mapper, warnings = self._load_items_definitions_for_config(cfg)
        self.id_mapper = id_mapper

        assets_folder = str(user_settings.get_client_assets_folder() or "").strip()
        if assets_folder and os.path.exists(assets_folder):
            self._set_assets_dir(assets_folder)

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
        try:
            self._sprite_cache.clear()
        except Exception:
            pass

        # One clear warning; after that keep it in the status bar.
        msg = (
            "Sprite rendering was temporarily disabled due to memory pressure/driver failure. "
            "You can keep editing (sprites may be hidden)."
        )
        try:
            self.status.showMessage(f"{msg} | reason={reason}")
        except Exception:
            pass

        if not bool(getattr(self, "_sprite_render_emergency_warned", False)):
            self._sprite_render_emergency_warned = True
            try:
                QMessageBox.warning(self, "Sprites disabled", f"{msg}\n\nReason: {reason}")
            except Exception:
                pass

    def _sprite_render_enabled(self: QtMapEditor) -> bool:
        if bool(getattr(self, "_sprite_render_temporarily_disabled", False)):
            return False
        return self.sprite_assets is not None and self.id_mapper is not None

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

        try:
            self.asset_profile = replace(profile, appearances_path=Path(path))
        except Exception:
            pass

        self._update_status_capabilities(prefix=f"Appearances loaded: {path}")

    def _unload_appearances_dat(self: QtMapEditor) -> None:
        self.appearance_assets = None
        profile = getattr(self, "asset_profile", None)
        if profile is not None and str(getattr(profile, "kind", "")).lower() == "modern":
            try:
                self.asset_profile = replace(profile, appearances_path=None)
            except Exception:
                pass
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
        if self.sprite_assets is None or self.id_mapper is None:
            return None
        cid = self.id_mapper.get_client_id(int(server_id))
        if cid is None or int(cid) <= 0:
            return None
        sprite_id = self._resolve_sprite_id_from_client_id(int(cid))
        if sprite_id is None or int(sprite_id) < 0:
            return None
        key = (int(sprite_id), int(tile_px))
        cached = self._sprite_cache.get(key)
        if cached is not None:
            # LRU bump
            try:
                self._sprite_cache.move_to_end(key)
            except Exception:
                pass
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
            # Insert into LRU, then enforce memory guard limits.
            try:
                self._sprite_cache[key] = pm
                self._sprite_cache.move_to_end(key)
            except Exception:
                # Fallback: still return pixmap even if cache bookkeeping fails.
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
                # Hard limit: evict aggressively to a target below hard.
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
        except SpriteAppearancesError as e:
            # Includes guarded failures from core sprite decoding/cache.
            self._disable_sprite_render_temporarily(reason=str(e))
            return None
        except Exception:
            return None

    def _sprite_bgra_for_server_id(self: QtMapEditor, server_id: int) -> tuple[int, int, int, bytes] | None:
        if not self._sprite_render_enabled():
            return None
        if self.sprite_assets is None or self.id_mapper is None:
            return None
        cid = self.id_mapper.get_client_id(int(server_id))
        if cid is None or int(cid) <= 0:
            return None
        sprite_id = self._resolve_sprite_id_from_client_id(int(cid))
        if sprite_id is None or int(sprite_id) < 0:
            return None
        try:
            w, h, bgra = self.sprite_assets.get_sprite_rgba(int(sprite_id))
            return (int(sprite_id), int(w), int(h), bgra)
        except MemoryError:
            self._disable_sprite_render_temporarily(reason="MemoryError while building sprite bytes")
            return None
        except SpriteAppearancesError as e:
            self._disable_sprite_render_temporarily(reason=str(e))
            return None
        except Exception:
            return None

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
                return

            # Get sprite count
            sprite_count = 0
            try:
                sprite_count = getattr(self.sprite_assets, "sprite_count", 0) or 0
            except Exception:
                pass

            if sprite_count <= 0:
                logger.debug("No sprites to hash")
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

        except ImportError:
            logger.warning("CrossVersionClipboard not available")
            self.sprite_matcher = None
        except Exception as e:
            logger.exception(f"Failed to build sprite hash database: {e}")
            self.sprite_matcher = None
