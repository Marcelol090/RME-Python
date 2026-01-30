# Version-Aware items.otb/items.xml Detection

## Overview

The map editor now automatically detects and loads version-specific item definition files (`items.otb` and `items.xml`) based on the Tibia client version. This matches RME's approach where each client version has its own data folder.

## Architecture

### Key Components

1. **ItemsOTBHeader** (`core/database/items_otb.py`)
   - Extracts client version from OTB file header
   - Parses CSD string (e.g., "OTB 3.65.62-13.10" → version 1310)
   - Fast header-only reading with `ItemsOTB.read_header()`

2. **ConfigurationManager** (`core/config/configuration_manager.py`)
   - Version-aware resolution of definition files
   - Auto-detection of client version from items.otb
   - Supports Canary format detection (OTBM v5+)

3. **MapVersionID** (`core/constants/otbm.py`)
   - Enum defining OTBM version identifiers
   - Distinguishes ServerID (v0-4) vs ClientID (v5-6) formats

## File Resolution Priority

The system searches for `items.otb` and `items.xml` in this order:

1. **Version-specific folder**: `data/{client_version}/items.otb`
   - Example: `data/1310/items.otb` for Tibia 13.10
   
2. **Engine-specific folder**: `data/{engine}/items.otb`
   - Example: `data/canary/items.otb`
   
3. **Generic folder**: `data/items/items.otb`
   - Fallback location with auto-version detection

## Client Version Detection

### From Project Metadata
```python
md = MapMetadata(engine='canary', client_version=1310, otbm_version=5, source='project')
cfg = ConfigurationManager.from_sniff(md, workspace_root=Path.cwd())
# Resolves to: data/1310/items.otb
```

### Auto-Detection from items.otb
```python
md = MapMetadata(engine='unknown', client_version=0, otbm_version=0, source='sniff')
cfg = ConfigurationManager.from_sniff(md, workspace_root=Path.cwd())
# Reads data/items/items.otb header
# Extracts version from CSD string
# detected_client_version: 1098 (from "OTB 3.57.62-10.98")
```

## OTBM Version Format Detection

### ServerID vs ClientID Format

```python
# Traditional format (OTBM v0-4): Stores ServerID
ConfigurationManager.is_canary_format(otbm_version=3)  # False

# Canary format (OTBM v5-6): Stores ClientID  
ConfigurationManager.is_canary_format(otbm_version=5)  # True
```

### Version Enum
```python
from core.constants import MapVersionID

MapVersionID.MAP_OTBM_1  # 0 - Tibia 7.4 (ServerID)
MapVersionID.MAP_OTBM_2  # 1 - Tibia 8.0 (ServerID)
MapVersionID.MAP_OTBM_3  # 2 - Tibia 8.4+ (ServerID)
MapVersionID.MAP_OTBM_4  # 3 - Tibia 8.7+ (ServerID)
MapVersionID.MAP_OTBM_5  # 4 - ClientID format
MapVersionID.MAP_OTBM_6  # 5 - ClientID format extended
```

## Data Flow

### Loading OTBM 5/6 Map (ClientID Format)

1. **IOMapOTBM::loadMap()** reads OTBM header, detects version 5/6
2. Sets `mapVersion.usesClientIdAsServerId = True`
3. For each item: reads **ClientID** from file
4. Calls `ItemIdMapper.clientToServer(clientId)` to get **ServerID**
5. Creates item with **ServerID** → Editor works with ServerIDs internally

### Saving to OTBM 5/6

1. **IOMapOTBM::saveMap()** checks `mapVersion.isCanaryFormat()`
2. For each item: gets **ServerID** from internal representation
3. Calls `ItemIdMapper.serverToClient(serverId)` to get **ClientID**
4. Writes **ClientID** to file

## ItemIdMapper Build Process

```python
def buildMappingsFromOtb(otb: ItemsOTB):
    """Build bidirectional ServerID ↔ ClientID mappings from items.otb."""
    for server_id, client_id in otb.server_to_client.items():
        # items.otb already contains both IDs!
        mapper.server_to_client[server_id] = client_id
        mapper.client_to_server[client_id] = server_id
```

## Why No appearances.dat Required?

- `items.otb` already contains **ClientIDs** in each entry
- **ServerID** and **ClientID** are both stored in OTB format
- `appearances.dat` is optional - only needed for extra sprite metadata
- Protobuf library included for future use if needed
- Mappings built at startup when client version loads

## Directory Structure Example

```
py_rme_canary/
├── data/
│   ├── 1010/          # Tibia 10.10
│   │   ├── items.otb
│   │   └── items.xml
│   ├── 1098/          # Tibia 10.98
│   │   ├── items.otb
│   │   └── items.xml
│   ├── 1310/          # Tibia 13.10
│   │   ├── items.otb
│   │   └── items.xml
│   ├── 1320/          # Tibia 13.20
│   │   ├── items.otb
│   │   └── items.xml
│   ├── items/         # Fallback (auto-detected)
│   │   ├── items.otb  
│   │   └── items.xml
│   └── brushes.json
```

## Usage Examples

### Example 1: Load Map with Known Version
```python
from core.io.otbm_loader import OTBMLoader
from pathlib import Path

loader = OTBMLoader()
game_map = loader.load_with_detection("maps/mymap.otbm", workspace_root=Path.cwd())

# Automatically resolves:
# - Client version from map metadata or items.otb header
# - items.otb from data/{version}/items.otb
# - items.xml from data/{version}/items.xml
# - Builds ItemIdMapper for ServerID ↔ ClientID translation
```

### Example 2: Check Version Format
```python
from core.config.configuration_manager import ConfigurationManager

# Check if map uses ClientID format (Canary)
is_canary = ConfigurationManager.is_canary_format(otbm_version=5)  # True
is_traditional = ConfigurationManager.is_canary_format(otbm_version=2)  # False
```

### Example 3: Manual Version Detection
```python
from core.database.items_otb import ItemsOTB

header = ItemsOTB.read_header("data/1310/items.otb")
print(f"Client Version: {header.client_version}")  # 1310
print(f"OTB Version: {header.major}.{header.minor}.{header.build}")  # 3.65.62
print(f"CSD: {header.csd}")  # "OTB 3.65.62-13.10"
```

## Benefits

1. **Automatic Version Matching**: No manual configuration needed
2. **Multi-Version Support**: Multiple Tibia versions coexist in data/ folder
3. **Backward Compatible**: Falls back to generic data/items/ folder
4. **Fast Detection**: Header-only reading for version extraction
5. **RME Compatibility**: Matches RME's version-per-folder approach

## Migration Guide

### From Old Structure
```
data/
└── items/
    ├── items.otb  # Generic version
    └── items.xml
```

### To New Structure
```
data/
├── 1310/
│   ├── items.otb  # Tibia 13.10
│   └── items.xml
├── 1320/
│   ├── items.otb  # Tibia 13.20
│   └── items.xml
└── items/         # Fallback
    ├── items.otb
    └── items.xml
```

Simply copy version-specific files from RME's data/ folder or your server's data folder.

## Reference

- **RME Source**: `source/iomap_otbm.cpp`, `source/items.cpp`
- **Technical Docs**: See image attachment showing ServerID vs ClientID explanation
- **OTBM Spec**: OTBM versions 0-4 (ServerID), 5-6 (ClientID)
