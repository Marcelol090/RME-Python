"""Asset Manager orchestration.

Handles loading of assets (sprites) and coordination between:
- SpriteAppearances (loading raw sprite sheets)
- SpriteCache (caching QPixmaps)
- IdMapper (converting ServerID <-> ClientID)
- ItemsOTB (server/client ID mapping from items.otb)
- ItemsXML (item names and metadata from items.xml)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtGui import QImage, QPixmap

from py_rme_canary.core.assets.loader import load_assets_from_path
from py_rme_canary.core.assets.sprite_appearances import SpriteAppearances
from py_rme_canary.core.database.id_mapper import IdMapper
from py_rme_canary.core.database.items_otb import ItemsOTB, ItemsOTBError
from py_rme_canary.core.database.items_xml import ItemsXML, ItemsXMLError, ItemType
from py_rme_canary.logic_layer.sprite_cache import SpriteCache

if TYPE_CHECKING:
    from py_rme_canary.core.assets.loader import SpriteProvider
    from py_rme_canary.core.memory_guard import MemoryGuard

logger = logging.getLogger(__name__)


class AssetManager:
    """Central manager for loading and accessing game assets."""

    _instance: AssetManager | None = None

    def __init__(self) -> None:
        self._sprite_appearances: SpriteAppearances | None = None
        self._sprite_provider: SpriteProvider | None = None
        self._id_mapper: IdMapper | None = None
        self._sprite_cache = SpriteCache.instance()
        self._assets_path: str | None = None
        self._is_loaded = False

        # Additional asset components for item metadata
        self._items_otb: ItemsOTB | None = None
        self._items_xml: ItemsXML | None = None
        self._client_version: int | None = None

    @classmethod
    def instance(cls) -> AssetManager:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        """Check if assets are loaded."""
        return self._is_loaded

    @property
    def assets_path(self) -> str | None:
        """Get currently loaded assets path."""
        return self._assets_path

    def load_assets(self, path: str | Path, memory_guard: MemoryGuard | None = None) -> bool:
        """Load assets from directory.

        Args:
            path: Path to assets directory (or client root)
            memory_guard: Optional memory guard

        Returns:
            True if loaded successfully
        """
        try:
            loaded = load_assets_from_path(path, memory_guard=memory_guard)
            self._sprite_provider = loaded.sprite_assets
            self._sprite_appearances = (
                loaded.sprite_assets if isinstance(loaded.sprite_assets, SpriteAppearances) else None
            )
            self._assets_path = str(loaded.profile.assets_dir or loaded.profile.root)
            self._is_loaded = True

            # Clear cache on new asset load
            self._sprite_cache.clear()

            if loaded.appearance_error:
                logger.warning("Appearances metadata unavailable: %s", loaded.appearance_error)
            if loaded.fallback_notice:
                logger.warning("%s", loaded.fallback_notice)

            logger.info("Assets loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load assets: {e}")
            self._sprite_provider = None
            self._sprite_appearances = None
            self._is_loaded = False
            return False

    def set_id_mapper(self, mapper: IdMapper | None) -> None:
        """Set or clear the ID mapper for Server<->Client conversion."""
        self._id_mapper = mapper

    def get_sprite(self, item_id: int, client_id_override: int | None = None) -> QPixmap | None:
        """Get sprite for an item (ServerID).

        Args:
            item_id: Server Item ID
            client_id_override: Optional direct Client ID

        Returns:
            QPixmap or None
        """
        if not self._is_loaded or not self._sprite_provider:
            return None

        # Check cache first (using server ID key)
        cached: Any = self._sprite_cache.get_sprite(item_id)
        if cached is not None:
            return QPixmap(cached) if not isinstance(cached, QPixmap) else cached

        # Resolve Client ID
        client_id = client_id_override
        if client_id is None:
            # Fallback: Assume 1:1 if no mapper (often wrong but better than nothing)
            client_id = self._id_mapper.get_client_id(item_id) if self._id_mapper else item_id

        if client_id is None or client_id == 0:
            return None

        # Load from SpriteAppearances
        try:
            width, height, bgra_data = self._sprite_provider.get_sprite_rgba(client_id)

            # Convert to QImage then QPixmap
            # Format_ARGB32 is actually BGRA in Qt's memory model usually,
            # but we need to check if we need to swap R/B.
            # SpriteAppearances returns BGRA.
            # QImage.Format.Format_ARGB32 expects B G R A (little endian) -> 0xAARRGGBB

            image = QImage(bgra_data, width, height, QImage.Format.Format_ARGB32)

            # Create isolated copy to detach from buffer
            pixmap = QPixmap.fromImage(image.copy())

            # Cache it
            self._sprite_cache.cache_sprite(item_id, pixmap)
            return pixmap

        except Exception:
            # logger.debug(f"Failed to load sprite for item {item_id} (client {client_id}): {e}")
            return None

    def get_item_name(self, server_id: int) -> str:
        """Get item name from items.xml.

        Args:
            server_id: Item server ID

        Returns:
            Item name or "Item #ID" if not found
        """
        if self._items_xml:
            item_type = self._items_xml.get(server_id)
            if item_type:
                return item_type.name
        return f"Item #{server_id}"

    def get_item_metadata(self, server_id: int) -> ItemType | None:
        """Get full item metadata from items.xml.

        Args:
            server_id: Item server ID

        Returns:
            ItemType or None if not found
        """
        if self._items_xml:
            return self._items_xml.get(server_id)
        return None

    def load_items_otb(self, otb_path: str | Path) -> bool:
        """Load items.otb for server/client ID mapping.

        Args:
            otb_path: Path to items.otb file

        Returns:
            True if loaded successfully
        """
        try:
            self._items_otb = ItemsOTB.load(otb_path)
            logger.info(f"Loaded items.otb: {len(self._items_otb.server_to_client)} mappings")

            # Create IdMapper from OTB mappings
            mapper = IdMapper(
                client_to_server=self._items_otb.client_to_server, server_to_client=self._items_otb.server_to_client
            )
            self.set_id_mapper(mapper)

            return True
        except (ItemsOTBError, FileNotFoundError) as e:
            logger.error(f"Failed to load items.otb: {e}")
            return False

    def load_items_xml(self, xml_path: str | Path) -> bool:
        """Load items.xml for item names and metadata.

        Args:
            xml_path: Path to items.xml file

        Returns:
            True if loaded successfully
        """
        try:
            self._items_xml = ItemsXML.load(xml_path, strict_mapping=False)
            logger.info(f"Loaded items.xml: {len(self._items_xml.items_by_server_id)} items")
            return True
        except (ItemsXMLError, FileNotFoundError) as e:
            logger.error(f"Failed to load items.xml: {e}")
            return False
