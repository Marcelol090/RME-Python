"""Magic bytes and OTB format constants.

Reference: source/items.h
"""

# OTB (items.otb) magic
MAGIC_OTBI = b"OTBI"

# Root attributes
ROOT_ATTR_VERSION = 0x01

# Item groups
ITEM_GROUP_DEPRECATED = 13

# Item attributes in OTB
ITEM_ATTR_FIRST = 0x10
ITEM_ATTR_SERVERID = ITEM_ATTR_FIRST
ITEM_ATTR_CLIENTID = ITEM_ATTR_FIRST + 1
