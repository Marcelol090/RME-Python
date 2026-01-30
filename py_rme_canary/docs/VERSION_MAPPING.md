# Tibia Version Mapping Reference

## OTBM Version Formats

| OTBM Ver | Enum Value | Tibia Versions | ID Format | Storage Format |
|----------|------------|----------------|-----------|----------------|
| 0        | MAP_OTBM_1 | 7.4 - 7.x      | ServerID  | Traditional    |
| 1        | MAP_OTBM_2 | 8.0 - 8.3x     | ServerID  | Traditional    |
| 2        | MAP_OTBM_3 | 8.4 - 8.6x     | ServerID  | Traditional    |
| 3        | MAP_OTBM_4 | 8.7 - 9.x      | ServerID  | Traditional    |
| 4        | MAP_OTBM_5 | 10.0+          | ClientID  | **Canary**     |
| 5        | MAP_OTBM_6 | 10.0+ (ext)    | ClientID  | **Canary**     |

## Client Version Numbering

Tibia uses `Major.Minor` format which is stored as `(Major * 100 + Minor)`:

| Folder | Tibia Version | Client ID | OTB CSD String | Notes |
|--------|---------------|-----------|---|----------|
| 740    | 7.4           | 740       | OTB 1.1.1 (1-byte aligned) | **Legacy** - no version in CSD |
| 800    | 8.0           | 800       | OTB 2.7.2-8.0 | First with version in CSD |
| 840    | 8.4           | 840       | OTB 3.12.7-8.40 | Note: 8.40 = 8.4 |
| 860    | 8.6           | 860       | OTB 3.20.20-8.60 | Note: 8.60 = 8.6 |
| 910    | 9.1           | 910       | OTB 3.28.31-9.10 |  |
| 920    | 9.2           | 920       | OTB 3.28.31-9.20 | Minor bump |
| 946    | 9.46          | 946       | OTB 3.36.46-9.46 |  |
| 960    | 9.6           | 960       | OTB 3.40.60-9.60 |  |
| 986    | 9.86          | 986       | OTB 3.46.86-9.86 |  |
| 1010   | 10.10         | 1010      | OTB 3.50.55-10.10 | First post-8x version |
| 1098   | 10.98         | 1098      | OTB 3.57.62-10.98 | Last 10.x? |
| 1271   | 12.71         | 1271      | OTB 3.58.62-12.71 | Jump to 12.x |
| 1310   | 13.10         | 1310      | OTB 3.65.62-13.10 | Current modern |
| 1320   | 13.20         | 1320      | OTB 3.66.62-13.20 |  |
| 1330   | 13.30         | 1330      | OTB 3.66.62-13.30 |  |

## Version Detection Strategy

### 1. From items.otb Header (Recommended)
```python
from core.database.items_otb import ItemsOTB

header = ItemsOTB.read_header("data/1310/items.otb")
client_version = header.client_version  # Automatically extracted
```

Extraction process:
1. Parse CSD string: `OTB X.Y.Z-{Major}.{Minor}`
2. Extract major/minor: e.g., "13.10" from "-13.10"
3. Calculate: `major * 100 + minor` = `1310`
4. Legacy fallback: If no CSD version, use mapping table (7.4 → 740)

### 2. From Map Metadata
```python
from core.config.configuration_manager import ConfigurationManager

is_canary = ConfigurationManager.is_canary_format(otbm_version=5)  # True
is_traditional = ConfigurationManager.is_canary_format(otbm_version=2)  # False
```

### 3. From File Path
```python
# Folder name = client version
# data/1310/ → version 1310
# data/840/  → version 840
# data/740/  → version 740
```

## Version Resolution Priority

ConfigurationManager searches in this order:

1. **Version-specific**: `data/{client_version}/items.otb`
   - Example: `data/1310/items.otb` ✅
   - Highest priority

2. **Engine-specific**: `data/{engine}/items.otb`
   - Example: `data/canary/items.otb`
   - Engine determined by `client_version >= 1300`

3. **Generic fallback**: `data/items/items.otb`
   - Auto-detects version from header
   - Lowest priority

## Traditional vs Canary Formats

### Traditional Format (OTBM 0-4)
- Stores **ServerID** in map files
- Editor works with ServerIDs
- Direct ID usage, no translation needed
- Used by older Tibia (7.4-9.86)

### Canary Format (OTBM 5-6)
- Stores **ClientID** in map files
- Loads: `ClientID → IdMapper → ServerID`
- Saves: `ServerID → IdMapper → ClientID`
- Used by modern Tibia (10.0+)

## ServerID vs ClientID

Example: Crystal Coin (modern Tibia 13.10)

```
items.otb:  ServerID=2160, ClientID=3043

Map File (traditional, ServerID):
    Item stores: 2160
    Editor shows: 2160

Map File (Canary, ClientID):
    Item stores: 3043
    Loads as: ClientID 3043 → ServerID 2160
    Editor shows: 2160 (internal representation)
    Saves as: ServerID 2160 → ClientID 3043
```

## Legacy OTB Mapping

For very old OTB files without client version in CSD:

| OTB Major.Minor | Tibia Client | Folder Name |
|-----------------|--------------|-------------|
| 1.1             | 7.4          | 740         |
| 1.2             | 7.5          | 750         |
| 2.x             | 8.0          | 800         |
| 3.x             | 8.4+         | 840, 860... |

## Discovery Timeline

- **7.4** (2001): First Tibia client version with items.otb
- **8.0** (2004): Version info added to OTB CSD string
- **8.4** (2005): ServerID ↔ ClientID mapping introduced
- **10.0** (2014): OTBM v4+ with ClientID format (Canary)
- **13.10** (2024): Modern Tibia with full ClientID support

## Data Structure Example

```
py_rme_canary/data/
├── 740/              # Tibia 7.4 (OTBM v0)
│   ├── items.otb
│   └── items.xml
├── 800/              # Tibia 8.0 (OTBM v1)
│   ├── items.otb
│   └── items.xml
├── 840/              # Tibia 8.4 (OTBM v2)
│   ├── items.otb
│   └── items.xml
├── 860/              # Tibia 8.6 (OTBM v2)
│   ├── items.otb
│   └── items.xml
├── 910/              # Tibia 9.1 (OTBM v3)
│   ├── items.otb
│   └── items.xml
├── 1010/             # Tibia 10.10 (OTBM v4+, ClientID)
│   ├── items.otb
│   └── items.xml
├── 1310/             # Tibia 13.10 (OTBM v5+, ClientID)
│   ├── items.otb
│   └── items.xml
├── items/            # Fallback (auto-detect)
│   ├── items.otb
│   └── items.xml
└── brushes.json
```

## Testing Version Detection

```python
# Test version extraction
from core.database.items_otb import ItemsOTB

versions = ['740', '800', '840', '860', '910', '1010', '1310']
for v in versions:
    header = ItemsOTB.read_header(f'data/{v}/items.otb')
    print(f"{v}: Detected={header.client_version}, CSD={header.csd}")
    assert header.client_version == int(v), f"Version mismatch for {v}"

print("✅ All version detections passed")
```

## References

- RME Source: `source/iomap_otbm.cpp`, `source/items.cpp`
- OTBM Specifications: OTBM versions 0-6
- Tibia Wiki: Client version history
