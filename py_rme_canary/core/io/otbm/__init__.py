"""OTBM I/O package - modular components for reading and writing OTBM files.

This package provides:
- streaming: Low-level byte stream reading with escape byte handling
- item_parser: Item attribute parsing and normalization
- tile_parser: Tile and house tile parsing
- header_parser: Root node and map header parsing
- loader: High-level map loading API
- saver: Map serialization to OTBM format
"""

# Streaming primitives
from .header_parser import RootHeader, read_root_header

# Parsers
from .item_parser import ItemParser

# High-level API - Loading
from .loader import (
    LoadWarning,
    OTBMLoader,
    load_game_map,
    load_game_map_with_items_db,
)

# High-level API - Saving
from .saver import (
    save_game_map_atomic,
    save_game_map_atomic_with_items_db,
    save_game_map_bundle_atomic,
    serialize,
)
from .streaming import (
    EscapedPayloadReader,
    begin_node,
    consume_siblings_until_end,
    read_exact,
    read_string,
    read_u8,
)
from .tile_parser import TileParser

__all__ = [
    # Streaming
    "EscapedPayloadReader",
    "read_exact",
    "read_u8",
    "begin_node",
    "consume_siblings_until_end",
    "read_string",
    # Parsers
    "ItemParser",
    "TileParser",
    "RootHeader",
    "read_root_header",
    # Loader
    "OTBMLoader",
    "LoadWarning",
    "load_game_map",
    "load_game_map_with_items_db",
    # Saver
    "serialize",
    "save_game_map_atomic",
    "save_game_map_atomic_with_items_db",
    "save_game_map_bundle_atomic",
]
