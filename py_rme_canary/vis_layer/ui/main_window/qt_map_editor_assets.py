from __future__ import annotations

import json
import os

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from py_rme_canary.core.assets.asset_profile import AssetProfileError, detect_asset_profile
from py_rme_canary.core.assets.loader import load_assets_from_profile
from py_rme_canary.core.assets.legacy_dat_spr import LegacySpriteError
from py_rme_canary.core.assets.sprite_appearances import SpriteAppearancesError
from py_rme_canary.core.config.project import find_project_for_otbm
from py_rme_canary.core.memory_guard import MemoryGuardError

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorAssetsMixin:
    # ---------- assets (legacy sprite sheets) ----------

    def _choose_assets_dir(self: "QtMapEditor") -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Tibia client folder or assets folder")
        if not path:
            return
        try:
            profile = detect_asset_profile(path)
            self._apply_asset_profile(profile)
        except (AssetProfileError, SpriteAppearancesError) as e:
            QMessageBox.critical(self, "Assets", str(e))

    def _set_assets_dir(self: "QtMapEditor", assets_dir: str) -> None:
        try:
            profile = detect_asset_profile(assets_dir)
        except AssetProfileError as e:
            QMessageBox.critical(self, "Assets", str(e))
            return
        self._apply_asset_profile(profile)

    def _apply_asset_profile(self: "QtMapEditor", profile) -> None:
        self.asset_profile = profile
        try:
            loaded = load_assets_from_profile(profile, memory_guard=self._memory_guard)
        except (AssetProfileError, SpriteAppearancesError, LegacySpriteError) as exc:
            QMessageBox.critical(self, "Assets", str(exc))
            return

        self.assets_dir = str(profile.assets_dir or profile.root)
        self.sprite_assets = loaded.sprite_assets
        self.appearance_assets = loaded.appearance_assets
        self._sprite_cache.clear()
        self._sprite_render_temporarily_disabled = False
        self._sprite_render_disabled_reason = None

        prefix_parts: list[str] = []
        if loaded.sheet_count is not None:
            prefix_parts.append(f"sheets: {loaded.sheet_count}")
        if loaded.sprite_count is not None:
            prefix_parts.append(f"sprites: {loaded.sprite_count}")
        prefix_suffix = f" ({', '.join(prefix_parts)})" if prefix_parts else ""
        self._update_status_capabilities(prefix=f"Assets loaded: {self.assets_dir}{prefix_suffix}")

        if loaded.appearance_error:
            self.status.showMessage(f"Appearances load failed: {loaded.appearance_error}")

        self._update_sprite_preview()

    def _apply_detected_context(self: "QtMapEditor", metadata: dict) -> None:
        prev_engine = str(self.engine)
        self.engine = str(metadata.get("engine") or "unknown")
        self.client_version = int(metadata.get("client_version") or 0)
        if self.engine != prev_engine:
            # Engine switch should never explode any downstream rendering.
            self._sprite_cache.clear()
            self._sprite_render_temporarily_disabled = False
            self._sprite_render_disabled_reason = None

    def _disable_sprite_render_temporarily(self: "QtMapEditor", *, reason: str) -> None:
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

    def _sprite_render_enabled(self: "QtMapEditor") -> bool:
        if bool(getattr(self, "_sprite_render_temporarily_disabled", False)):
            return False
        return self.sprite_assets is not None and self.id_mapper is not None

    def _update_status_capabilities(self: "QtMapEditor", *, prefix: str = "") -> None:
        assets = "ON" if self.sprite_assets is not None else "OFF"
        mapping = "ON" if self.id_mapper is not None else "OFF"
        appearances = "ON" if self.appearance_assets is not None else "OFF"
        sprite = "ON" if self._sprite_render_enabled() else "OFF"
        profile = getattr(self, "asset_profile", None)
        profile_kind = str(getattr(profile, "kind", "none"))
        engine = str(self.engine or "unknown")
        cv = int(self.client_version or 0)
        cap = (
            f"engine={engine} client={cv} | profile={profile_kind} assets={assets} "
            f"appearances={appearances} mapping={mapping} sprite={sprite}"
        )
        msg = f"{prefix} | {cap}" if prefix else cap
        self.status.showMessage(msg)

    def _resolve_sprite_id_from_client_id(self: "QtMapEditor", client_id: int) -> int | None:
        if self.appearance_assets is None:
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

    def _maybe_write_default_project_json(self: "QtMapEditor", *, opened_otbm_path: str, cfg) -> None:
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

    def _sprite_pixmap_for_server_id(self: "QtMapEditor", server_id: int, *, tile_px: int) -> QPixmap | None:
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

    def _sprite_bgra_for_server_id(
        self: "QtMapEditor", server_id: int
    ) -> tuple[int, int, int, bytes] | None:
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

    def _update_sprite_preview(self: "QtMapEditor") -> None:
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
