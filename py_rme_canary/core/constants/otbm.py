"""OTBM format constants.

Node delimiters, node types, and attribute identifiers for OTBM parsing.

Reference: source/iomap_otbm.h
"""

from enum import IntEnum


# OTBM Version Identifiers
# These determine whether item IDs in the map file are ServerID (0-4) or ClientID (5+)
class MapVersionID(IntEnum):
    """OTBM map format version identifiers.

    Versions 0-4 store ServerID (traditional format).
    Versions 5-6 store ClientID (Canary format).
    """

    MAP_OTBM_1 = 0  # 7.4 - Traditional (ServerID)
    MAP_OTBM_2 = 1  # 8.0 - Traditional (ServerID)
    MAP_OTBM_3 = 2  # 8.4+ - Traditional (ServerID)
    MAP_OTBM_4 = 3  # 8.7+ - Traditional (ServerID)
    MAP_OTBM_5 = 4  # ClientID format
    MAP_OTBM_6 = 5  # ClientID format extended


# Node stream delimiters
NODE_START = 0xFE
NODE_END = 0xFF
ESCAPE_CHAR = 0xFD

# Magic bytes
MAGIC_OTBM = b"OTBM"
MAGIC_WILDCARD = b"\x00\x00\x00\x00"

# Node types
OTBM_ROOTV1 = 0x01
OTBM_MAP_DATA = 0x02
OTBM_TILE_AREA = 0x04
OTBM_TILE = 0x05
OTBM_ITEM = 0x06
OTBM_TOWNS = 0x0C
OTBM_TOWN = 0x0D
OTBM_HOUSETILE = 0x0E
OTBM_WAYPOINTS = 0x0F
OTBM_WAYPOINT = 0x10
OTBM_TILE_ZONE = 0x13

# MAP_DATA attributes
OTBM_ATTR_DESCRIPTION = 1
OTBM_ATTR_EXT_SPAWN_MONSTER_FILE = 11
OTBM_ATTR_EXT_HOUSE_FILE = 13
OTBM_ATTR_EXT_SPAWN_NPC_FILE = 23
OTBM_ATTR_EXT_ZONE_FILE = 24

# TILE attributes
OTBM_ATTR_TILE_FLAGS = 3
OTBM_ATTR_ITEM = 9

# ITEM attributes
OTBM_ATTR_ACTION_ID = 4
OTBM_ATTR_UNIQUE_ID = 5
OTBM_ATTR_TEXT = 6
OTBM_ATTR_DESC = 7
OTBM_ATTR_TELE_DEST = 8
OTBM_ATTR_DEPOT_ID = 10
OTBM_ATTR_RUNE_CHARGES = 12
OTBM_ATTR_HOUSEDOORID = 14
OTBM_ATTR_COUNT = 15
OTBM_ATTR_CHARGES = 22

# Extended attributes
OTBM_ATTR_ATTRIBUTE_MAP = 128

# Server-side attributes (not used by RME but may appear in maps saved by game servers)
# These are defined for documentation and future compatibility only
OTBM_ATTR_EXT_FILE = 2  # Legacy/deprecated
OTBM_ATTR_DURATION = 16  # Item duration timer
OTBM_ATTR_DECAYING_STATE = 17  # Item decay state
OTBM_ATTR_WRITTENDATE = 18  # Written date for books
OTBM_ATTR_WRITTENBY = 19  # Author of written text
OTBM_ATTR_SLEEPERGUID = 20  # Bed sleeper GUID
OTBM_ATTR_SLEEPSTART = 21  # Bed sleep start time
