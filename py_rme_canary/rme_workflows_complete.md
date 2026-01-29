# 🎯 RME Multi-LLM Workflows & Rules - Guia Completo

## 📚 Índice

1. [Cursor IDE - GPT-Codex](#cursor-ide---gpt-codex)
2. [Antigravity - Sonnet 4.5](#antigravity---sonnet-45)
3. [Antigravity - Opus 4.5](#antigravity---opus-45)
4. [Antigravity - Gemini 3](#antigravity---gemini-3)
5. [Workflows Especializados](#workflows-especializados)
6. [Rules Avançadas](#rules-avançadas)

---

# Cursor IDE - GPT-Codex

## `.cursor/rules/` - Rules Completas

### `otbm_format_deep.mdc`

```markdown
# OTBM Format - Deep Dive Rules

## Critical Knowledge Base

### Escape Sequence System (NEVER FORGET)
```python
# OTBM uses 3 special bytes
OTBM_NODE_START = 0xFD  # Marks node beginning
OTBM_NODE_END   = 0xFE  # Marks node end
OTBM_ESCAPE     = 0xFF  # Next byte is literal

# Example: Reading with escapes
def read_byte_escaped(stream: BinaryIO) -> int:
    byte = stream.read(1)[0]
    if byte == OTBM_ESCAPE:
        # 0xFF means "next byte is literal"
        # So 0xFF 0xFD means literal 0xFD (not node start)
        return stream.read(1)[0]
    return byte

# Example: Writing with escapes
def write_byte_escaped(stream: BinaryIO, value: int) -> None:
    if value in (0xFD, 0xFE, 0xFF):
        stream.write(bytes([0xFF, value]))  # Escape it
    else:
        stream.write(bytes([value]))
```

### Node Structure
```
[0xFD] [NodeType] [Properties...] [Children...] [0xFE]
       ^1 byte    ^variable        ^recursive   ^end marker
```

**Example: OTBM_MAP_HEADER**
```
FD                    # Node start
00                    # Node type (OTBM_MAP_HEADER)
01 00                 # Version (little-endian uint16 = 1)
10 00                 # Width (uint16 = 16)
10 00                 # Height (uint16 = 16)
04 00 00 00           # Major items version (uint32 = 4)
01 00 00 00           # Minor items version (uint32 = 1)
FE                    # Node end
```

### Attribute System
Items have attributes stored as TLV (Type-Length-Value):
```python
ATTR_DESCRIPTION = 0x01
ATTR_EXT_FILE = 0x02
ATTR_TILE_FLAGS = 0x03
ATTR_ACTION_ID = 0x04
ATTR_UNIQUE_ID = 0x05
ATTR_TEXT = 0x06
ATTR_DESC = 0x07
ATTR_TELE_DEST = 0x08
ATTR_ITEM = 0x09
ATTR_DEPOT_ID = 0x0A
ATTR_SPAWN_FILE = 0x0B
ATTR_RUNE_CHARGES = 0x0C
ATTR_HOUSE_FILE = 0x0D
ATTR_HOUSEDOORID = 0x0E
ATTR_COUNT = 0x0F
ATTR_DURATION = 0x10
ATTR_DECAYING_STATE = 0x11
ATTR_WRITTENDATE = 0x12
ATTR_WRITTENBY = 0x13
ATTR_SLEEPERGUID = 0x14
ATTR_SLEEPSTART = 0x15
ATTR_CHARGES = 0x16

# Reading attribute
def read_attribute(stream: BinaryIO) -> tuple[int, bytes]:
    attr_type = read_byte_escaped(stream)

    if attr_type == ATTR_TEXT:
        length = struct.unpack('<H', stream.read(2))[0]
        value = stream.read(length)
    elif attr_type == ATTR_ACTION_ID:
        value = struct.unpack('<H', stream.read(2))[0]
    # ... more types

    return attr_type, value
```

### Validation Rules

**ALWAYS validate:**
1. Node nesting depth (max 16 levels recommended)
2. Proper node closure (every FD has matching FE)
3. Attribute bounds (no overflow)
4. Position validity (x, y within map bounds)

```python
class OTBMValidator:
    def validate_node_depth(self, depth: int) -> None:
        if depth > 16:
            raise OTBMError(f"Node depth {depth} exceeds limit 16")

    def validate_position(self, x: int, y: int, z: int) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise OTBMError(f"Position ({x}, {y}, {z}) out of bounds")
        if not (0 <= z <= 15):
            raise OTBMError(f"Z-level {z} invalid (must be 0-15)")
```

## Performance Hot Paths

### Streaming Parser (Required for Large Maps)
```python
class OTBMStreamingParser:
    def __init__(self, file: BinaryIO):
        self.file = file
        self.node_stack = []

    def parse(self) -> Iterator[OTBMNode]:
        """Yield nodes as they're parsed (memory efficient)."""
        while True:
            try:
                node = self._read_node()
                if node:
                    yield node
                else:
                    break
            except EOFError:
                break

    def _read_node(self) -> Optional[OTBMNode]:
        marker = read_byte_escaped(self.file)
        if marker != OTBM_NODE_START:
            return None

        node_type = read_byte_escaped(self.file)
        properties = self._read_properties(node_type)

        # Don't load children into memory - yield them lazily
        return OTBMNode(type=node_type, properties=properties)
```

### Caching Strategy
```python
from functools import lru_cache

@lru_cache(maxsize=10000)
def get_item_flags(item_id: int) -> int:
    """Cache item flags to avoid repeated database lookups."""
    return items_db.get_flags(item_id)
```

## Error Handling Patterns

```python
class OTBMError(Exception):
    """Base OTBM error."""
    pass

class OTBMVersionError(OTBMError):
    """Unsupported OTBM version."""
    pass

class OTBMCorruptionError(OTBMError):
    """Corrupted OTBM file."""
    pass

# Usage
try:
    game_map = loader.load("map.otbm")
except OTBMVersionError as e:
    logger.error(f"Unsupported version: {e}")
    raise
except OTBMCorruptionError as e:
    logger.error(f"Corrupted file: {e}")
    # Try recovery mode
    game_map = loader.load_partial("map.otbm")
```

## Testing Patterns

```python
# Always test with real OTBM samples
def test_load_real_otbm():
    \"\"\"Test with actual RME-generated map.\"\"\"
    loader = OTBMLoader()
    game_map = loader.load("tests/fixtures/realmap.otbm")

    assert game_map.width == 256
    assert game_map.height == 256
    assert len(game_map.tiles) > 0

# Test escape sequences specifically
def test_escape_sequences():
    \"\"\"Test reading/writing escape sequences.\"\"\"
    # Create buffer with escaped bytes
    buf = BytesIO(bytes([0xFF, 0xFD, 0xFF, 0xFE, 0xFF, 0xFF]))

    # Should read as: 0xFD, 0xFE, 0xFF (literals)
    assert read_byte_escaped(buf) == 0xFD
    assert read_byte_escaped(buf) == 0xFE
    assert read_byte_escaped(buf) == 0xFF
```

## References
- OTBM Spec: https://otland.net/threads/otbm-format.236677/
- RME Source: `source/iomap_otbm.cpp`
- TFS Source: `src/iomap.cpp`
```

### `performance_critical.mdc`

```markdown
# Performance-Critical Rules

## Hot Path Identification

**These functions are called THOUSANDS of times per frame:**
1. `get_tile(x, y, z)` - Map lookups
2. `get_border_variant(ground_id, mask)` - Auto-border
3. `render_tile(tile, x, y)` - Rendering
4. `compute_neighbor_mask(pos)` - Brush system

## Optimization Patterns

### 1. Use __slots__ (Memory + Speed)
```python
@dataclass(frozen=True, slots=True)
class Position:
    x: int
    y: int
    z: int

# Saves 40-50% memory + faster attribute access
```

### 2. LRU Cache for Pure Functions
```python
from functools import lru_cache

@lru_cache(maxsize=1024)
def get_border_variant(ground_id: int, mask: int) -> int:
    \"\"\"Cached border lookup (called millions of times).\"\"\"
    return BORDER_LOOKUP[ground_id][mask]
```

### 3. Spatial Indexing for Tile Lookups
```python
class GameMap:
    def __init__(self):
        # Use dict with (x, y, z) tuple as key
        self._tiles: dict[tuple[int, int, int], Tile] = {}

        # NOT list[list[list[Tile]]] - wastes memory on sparse maps

    def get_tile(self, x: int, y: int, z: int) -> Optional[Tile]:
        return self._tiles.get((x, y, z))  # O(1) lookup
```

### 4. Generators for Large Datasets
```python
def iter_tiles(self) -> Iterator[tuple[Position, Tile]]:
    \"\"\"Yield tiles lazily (don't load all into memory).\"\"\"
    for (x, y, z), tile in self._tiles.items():
        yield Position(x, y, z), tile

# Usage
for pos, tile in game_map.iter_tiles():
    if tile.ground:
        process(tile)  # Processes one at a time
```

## Profiling Commands
```bash
# Profile with cProfile
python -m cProfile -o profile.stats main.py

# Analyze with snakeviz
snakeviz profile.stats

# Line-by-line profiling
kernprof -l -v slow_function.py
```

## Benchmarking
```python
# Always benchmark optimizations
import timeit

def benchmark_tile_lookup():
    setup = \"\"\"
from py_rme_canary.core.data.gamemap import GameMap
game_map = GameMap()
# ... populate map
\"\"\"

    # Old method
    old = timeit.timeit(
        "game_map.get_tile_slow(100, 100, 7)",
        setup=setup,
        number=100000
    )

    # New method
    new = timeit.timeit(
        "game_map.get_tile(100, 100, 7)",
        setup=setup,
        number=100000
    )

    print(f"Speedup: {old/new:.2f}x")
```
```

---

## `.cursor/commands/` - Slash Commands

### `~/.cursor/commands/rme.json`

```json
{
  "rme-fix-imports": {
    "description": "Fix layer violation imports",
    "prompt": "Analyze imports and fix layer violations:\n1. Scan for illegal imports (core→logic/vis, logic→vis)\n2. Move code to correct layer OR use Protocol\n3. Update all references\n4. Run: grep -r 'from.*vis_layer' core/ logic_layer/\n5. Verify no circular imports with pydeps"
  },

  "rme-add-tests": {
    "description": "Add comprehensive tests for module",
    "prompt": "Create tests for selected module:\n1. Unit tests (pytest)\n2. Edge cases (None, empty, overflow)\n3. Error cases (exceptions)\n4. Property-based tests (hypothesis) if applicable\n5. Achieve 90%+ coverage\n6. Mock external dependencies"
  },

  "rme-benchmark": {
    "description": "Add performance benchmark",
    "prompt": "Create benchmark for selected function:\n1. Use pytest-benchmark\n2. Test with realistic data sizes\n3. Set regression threshold\n4. Document expected performance\n5. Add to CI pipeline"
  },

  "rme-refactor-dataclass": {
    "description": "Refactor class to frozen dataclass",
    "prompt": "Convert selected class to frozen dataclass:\n1. Identify all attributes\n2. Create @dataclass(frozen=True, slots=True)\n3. Convert mutations to replace()\n4. Update all usage sites\n5. Run tests to verify\n6. Document immutability benefits"
  },

  "rme-optimize-hotpath": {
    "description": "Optimize performance-critical code",
    "prompt": "Optimize selected code:\n1. Profile with cProfile/line_profiler\n2. Add @lru_cache for pure functions\n3. Use __slots__ in dataclasses\n4. Replace lists with generators if appropriate\n5. Benchmark before/after\n6. Document speedup in commit message"
  },

  "rme-port-cpp": {
    "description": "Port C++ code from RME/TFS/Canary",
    "prompt": "Port C++ implementation to Python:\n1. Locate C++ source (provide file:line)\n2. Extract algorithm (ignore memory management)\n3. Design Python equivalent with type hints\n4. Write tests FIRST (TDD)\n5. Validate behavior matches C++\n6. Document C++ source in docstring"
  },

  "rme-security-audit": {
    "description": "Security audit for file I/O code",
    "prompt": "Audit security of selected code:\n1. Check path traversal vulnerabilities\n2. Validate all user inputs\n3. Add file size limits (MemoryGuard)\n4. Use atomic writes (prevent corruption)\n5. Add error handling\n6. Run bandit security linter"
  }
}
```

---

# Antigravity - Sonnet 4.5

## `.agent/workflows/` - Workflows Especializados

### `implement-otbm-parser.md`

```markdown
---
description: Implement OTBM format parser component
scope: Single parser (header, tile, item, etc)
duration: 3-4 hours
---

## Steps

### 1. UNDERSTAND OTBM Format (30min)
**Read specifications:**
- OTBM escape sequences (0xFD, 0xFE, 0xFF)
- Node structure (type, properties, children)
- Attribute system (TLV encoding)

**Reference C++ implementation:**
```cpp
// RME: source/iomap_otbm.cpp
bool IOMapOTBM::loadMap(Map* map, const FileName& identifier) {
    // ...
    uint8_t byte;
    while(f.getByte(byte)) {
        if(byte == 0xFF) {  // Escape
            f.getByte(byte);
        }
        // ... process byte
    }
}
```

### 2. DESIGN Parser (45min)
**Structure:**
```python
# core/io/otbm/tile_parser.py
from __future__ import annotations
from dataclasses import dataclass
from typing import BinaryIO

from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.io.otbm.streaming import read_byte_escaped

class TileParser:
    def __init__(self, items_db: ItemsXML):
        self.items_db = items_db

    def parse_tile(self, stream: BinaryIO) -> Tile:
        \"\"\"Parse tile node from OTBM stream.

        OTBM Structure:
        [0xFD] [OTBM_TILE] [x:u16] [y:u16] [z:u8] [attrs...] [items...] [0xFE]

        Args:
            stream: Binary stream positioned at tile node

        Returns:
            Parsed Tile object

        References:
            RME: source/iomap_otbm.cpp:456
        \"\"\"
        # TODO: Implement
        pass
```

### 3. IMPLEMENT with TDD (2h)
**Test FIRST:**
```python
# test_tile_parser.py
import struct
from io import BytesIO

def test_parse_tile_basic():
    \"\"\"Test parsing basic tile (ground only).\"\"\"
    # Create OTBM tile node
    buf = BytesIO()
    buf.write(bytes([0xFD]))  # Node start
    buf.write(bytes([0x00]))  # OTBM_TILE
    buf.write(struct.pack('<H', 100))  # x
    buf.write(struct.pack('<H', 100))  # y
    buf.write(bytes([7]))  # z
    buf.write(bytes([0xFE]))  # Node end
    buf.seek(0)

    parser = TileParser(items_db)
    tile = parser.parse_tile(buf)

    assert tile.position == Position(100, 100, 7)

def test_parse_tile_with_items():
    \"\"\"Test parsing tile with items.\"\"\"
    # ... create OTBM data with items
    tile = parser.parse_tile(buf)

    assert len(tile.items) > 0

def test_parse_tile_with_escape():
    \"\"\"Test handling escape sequences.\"\"\"
    # Create tile with escaped byte (e.g., item ID 0xFD)
    buf = BytesIO()
    buf.write(bytes([0xFF, 0xFD]))  # Escaped 0xFD
    buf.seek(0)

    value = read_byte_escaped(buf)
    assert value == 0xFD
```

**Implement until tests pass**

### 4. INTEGRATE (30min)
```python
# core/io/otbm/loader.py
class OTBMLoader:
    def load(self, path: Path) -> GameMap:
        with open(path, 'rb') as f:
            # ... parse header

            # Use TileParser
            tile_parser = TileParser(self.items_db)

            while not eof:
                node_type = read_byte_escaped(f)
                if node_type == OTBM_TILE:
                    tile = tile_parser.parse_tile(f)
                    game_map.add_tile(tile)
```

### 5. VALIDATE (15min)
**Load real RME map:**
```python
def test_load_rme_map():
    \"\"\"Integration test with real RME map.\"\"\"
    loader = OTBMLoader(items_db)
    game_map = loader.load("tests/fixtures/forgotten.otbm")

    assert game_map.width > 0
    assert len(game_map.tiles) > 0

    # Spot check specific tile
    tile = game_map.get_tile(1000, 1000, 7)
    assert tile is not None
```

### 6. COMMIT (5min)
```bash
git add core/io/otbm/tile_parser.py tests/
git commit -m "feat(otbm): add tile parser

- Handles escape sequences correctly
- Parses position (x, y, z)
- Parses items and attributes
- Tests: test_tile_parser.py (100% coverage)
- References: RME source/iomap_otbm.cpp:456
"
```

## Quality Gates
- ✅ Escape sequences handled correctly
- ✅ Tests pass with real OTBM data
- ✅ mypy --strict (0 errors)
- ✅ Coverage ≥90%

## References
- OTBM Spec: https://otland.net/threads/otbm-format.236677/
- RME Source: `source/iomap_otbm.cpp`
```

### `implement-brush.md`

```markdown
---
description: Implement new brush type
scope: Single brush (Ground, Wall, Doodad, etc)
duration: 2-3 hours
---

## Steps

### 1. RESEARCH RME Implementation (30min)
**Locate C++ brush:**
```bash
cd rme/
grep -r "class.*Brush" source/
```

**Key files:**
- `source/baseBrush.h` - Base interface
- `source/groundBrush.cpp` - Ground implementation
- `source/wallBrush.cpp` - Wall implementation

**Example C++ brush:**
```cpp
// source/groundBrush.cpp
void GroundBrush::draw(BaseMap* map, Tile* tile, void* parameter) {
    uint32_t ground_id = getItemID();

    // Auto-border: check 8 neighbors
    uint32_t border_mask = 0;
    for(int i = 0; i < 8; ++i) {
        Tile* neighbor = map->getTile(tile->getPosition() + directions[i]);
        if(neighbor && matchesGround(neighbor)) {
            border_mask |= (1 << i);
        }
    }

    // Lookup border variant
    uint32_t border_id = borderLookup[ground_id][border_mask];
    tile->addItem(Item::Create(border_id));
}
```

### 2. DESIGN Python Equivalent (30min)
```python
# logic_layer/brushes/ground_brush.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.position import Position
from py_rme_canary.logic_layer.brushes.base_brush import BaseBrush

@dataclass(frozen=True, slots=True)
class GroundBrush(BaseBrush):
    \"\"\"Ground brush with auto-bordering.

    Attributes:
        ground_id: Base ground item ID
        border_group: Border group for lookups

    References:
        RME: source/groundBrush.cpp
    \"\"\"
    ground_id: int
    border_group: str

    def apply(
        self,
        game_map: GameMap,
        pos: Position
    ) -> list[TileDelta]:
        \"\"\"Apply ground with auto-border.

        Algorithm:
        1. Check 8 neighbors
        2. Compute border mask (8-bit)
        3. Lookup border variant
        4. Place item on tile

        Args:
            game_map: Target map
            pos: Position to paint

        Returns:
            List of tile modifications for undo/redo
        \"\"\"
        tile = game_map.get_or_create_tile(pos)

        # Compute border mask
        mask = self._compute_neighbor_mask(game_map, pos)

        # Lookup border variant
        border_id = get_border_variant(self.ground_id, mask)

        # Create delta for undo
        old_tile = tile.copy()

        # Apply ground
        tile.ground = Item(id=border_id)

        return [TileDelta(pos=pos, old=old_tile, new=tile)]

    def _compute_neighbor_mask(
        self,
        game_map: GameMap,
        pos: Position
    ) -> int:
        \"\"\"Compute 8-neighbor border mask.\"\"\"
        mask = 0
        for i, (dx, dy) in enumerate(DIRECTIONS_8):
            neighbor_pos = Position(pos.x + dx, pos.y + dy, pos.z)
            neighbor = game_map.get_tile(neighbor_pos)

            if neighbor and self._matches_ground(neighbor):
                mask |= (1 << i)

        return mask

    def _matches_ground(self, tile: Tile) -> bool:
        \"\"\"Check if tile has matching ground.\"\"\"
        if not tile.ground:
            return False
        return tile.ground.id in BORDER_FRIENDS[self.border_group]
```

### 3. IMPLEMENT with TDD (1h)
**Test FIRST:**
```python
# test_ground_brush.py
def test_ground_brush_isolated():
    \"\"\"Test ground brush on isolated tile (no neighbors).\"\"\"
    game_map = GameMap()
    brush = GroundBrush(ground_id=4526, border_group="grass")
    pos = Position(100, 100, 7)

    deltas = brush.apply(game_map, pos)

    assert len(deltas) == 1
    tile = game_map.get_tile(pos)
    assert tile.ground.id == 4526  # Base grass

def test_ground_brush_with_neighbors():
    \"\"\"Test auto-border with neighbors.\"\"\"
    game_map = GameMap()
    brush = GroundBrush(ground_id=4526, border_group="grass")

    # Place grass tiles in pattern
    #   G G G
    #   G X G  <- X is target
    #   G G G
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue  # Skip center
            pos = Position(100 + dx, 100 + dy, 7)
            game_map.set_tile(pos, Tile(ground=Item(id=4526)))

    # Apply brush to center
    center = Position(100, 100, 7)
    deltas = brush.apply(game_map, center)

    tile = game_map.get_tile(center)
    # Should use inner grass variant (all neighbors match)
    assert tile.ground.id != 4526  # Not base grass
    assert tile.ground.id in range(4526, 4600)  # Border variant

def test_ground_brush_undo():
    \"\"\"Test undo system integration.\"\"\"
    game_map = GameMap()
    brush = GroundBrush(ground_id=4526, border_group="grass")
    pos = Position(100, 100, 7)

    # Apply brush
    deltas = brush.apply(game_map, pos)

    # Undo
    for delta in reversed(deltas):
        delta.undo(game_map)

    # Should be back to empty
    tile = game_map.get_tile(pos)
    assert tile is None or tile.ground is None
```

**Implement until tests pass**

### 4. INTEGRATE with BrushManager (30min)
```python
# logic_layer/brush_definitions.py
class BrushManager:
    def create_ground_brush(
        self,
        ground_id: int,
        border_group: str
    ) -> GroundBrush:
        \"\"\"Factory method for ground brushes.\"\"\"
        return GroundBrush(
            ground_id=ground_id,
            border_group=border_group
        )
```

### 5. VALIDATE (10min)
**Manual test in UI:**
```python
# In QtMapEditor
brush = brush_mgr.create_ground_brush(4526, "grass")
session.set_selected_brush(brush)
# Paint on canvas and verify auto-border works
```

### 6. COMMIT (5min)
```bash
git add logic_layer/brushes/ground_brush.py tests/
git commit -m "feat(brush): implement ground brush with auto-border

- Auto-border algorithm from RME source
- 8-neighbor detection
- Border mask lookup
- Undo/redo support via TileDelta
- Tests: test_ground_brush.py (100% coverage)
- References: RME source/groundBrush.cpp:123
"
```

## Quality Gates
- ✅ Auto-border works correctly
- ✅ Undo/redo functional
- ✅ Tests pass (pytest)
- ✅ Type hints (mypy --strict)

## References
- RME Brushes: `source/*Brush.cpp`
```

---

# Antigravity - Opus 4.5

## `.anthropic/workflows/opus/` - Workflows de Arquitetura

### `design-live-collaboration.md`

```markdown
---
description: Design live collaboration system (multi-user map editing)
scope: Network protocol, synchronization, conflict resolution
duration: 2-3 days
complexity: Very High
---

## DEEP Framework

### 1. DISCOVER (4h) - Problem Analysis

**Problem Statement:**
Enable multiple users to edit the same map simultaneously with real-time synchronization.

**Key Challenges:**
1. **Conflict Resolution:** Two users paint same tile simultaneously
2. **Network Latency:** 50-500ms RTT
3. **State Synchronization:** Keep all clients in sync
4. **Undo/Redo:** Distributed action queue
5. **Scalability:** Support 2-10 concurrent editors

**Requirements:**
- Real-time updates (<200ms)
- Eventual consistency (CRDT-based)
- Fair conflict resolution
- Full undo/redo support
- Bandwidth efficient (<100 KB/s per user)

**Deliverable:** Requirements document

### 2. EXPLORE (8h) - Research Phase

**Study Existing Solutions:**

**A) Operational Transformation (OT)**
- Used by Google Docs
- Complex to implement correctly
- Good for linear data (text)
- Harder for 2D/3D data (maps)

**B) Conflict-free Replicated Data Types (CRDT)**
- Used by Figma, Redis
- Mathematically provable convergence
- Better for spatial data
- Examples: LWW-Element-Set, OR-Set

**C) Centralized Server with Locking**
- Simple but slow
- User must "lock" area to edit
- No conflicts but poor UX

**Decision:** Use **CRDT-based approach** with centralized server for authority

**CRDT Design:**
```python
# Each tile edit is a CRDT operation
@dataclass(frozen=True, slots=True)
class TileOperation:
    op_id: UUID  # Unique operation ID
    timestamp: int  # Lamport timestamp
    user_id: str
    position: Position
    action: str  # "set_ground", "add_item", etc
    data: dict[str, Any]

    def __lt__(self, other: TileOperation) -> bool:
        # Total order: timestamp, then op_id
        if self.timestamp != other.timestamp:
            return self.timestamp < other.timestamp
        return self.op_id < other.op_id

# CRDT: Last-Write-Wins Element Set
class LWWTileSet:
    def __init__(self):
        self.operations: list[TileOperation] = []

    def apply(self, op: TileOperation) -> None:
        self.operations.append(op)
        self.operations.sort()  # Maintain total order

    def compute_state(self, pos: Position) -> Tile:
        # Apply operations in order
        tile = Tile()
        for op in self.operations:
            if op.position == pos:
                tile = op.apply_to(tile)
        return tile
```

**Network Protocol:**
```python
# WebSocket-based protocol
{
  "type": "tile_operation",
  "op_id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": 1234567890,
  "user_id": "user_alice",
  "position": {"x": 100, "y": 100, "z": 7},
  "action": "set_ground",
  "data": {"ground_id": 4526}
}
```

**Deliverable:** Architecture decision document

### 3. ENGINEER (12h) - Detailed Design

**System Architecture:**
```
â"Œâ"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"
â"‚  Client (RME Editor)       â"‚
â"‚  ────────────────────      â"‚
â"‚  - Local GameMap state     â"‚
â"‚  - Outgoing operation queue│
â"‚  - Incoming operation queue│
â"‚  - Synchronization manager â"‚
â""â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"¬â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"˜
           â"‚ WebSocket
           â"‚
â"Œâ"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"¼â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"
â"‚  Server (FastAPI)          â"‚
â"‚  ────────────────────      â"‚
â"‚  - Operation log (CRDT)    â"‚
â"‚  - Connected clients list  â"‚
â"‚  - Broadcast manager       â"‚
â"‚  - Persistence (SQLite)    â"‚
â""â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"˜
```

**Component Design:**

**A) Client Synchronization Manager**
```python
# logic_layer/live/sync_manager.py
class SyncManager:
    def __init__(self, game_map: GameMap, server_url: str):
        self.game_map = game_map
        self.server_url = server_url
        self.ws: Optional[WebSocket] = None

        # CRDT operation log
        self.operations: list[TileOperation] = []

        # Pending operations (not yet acknowledged)
        self.pending: list[TileOperation] = []

        # Lamport clock for ordering
        self.clock = 0

    async def connect(self) -> None:
        self.ws = await websockets.connect(self.server_url)
        asyncio.create_task(self._receive_loop())

    async def apply_local_edit(
        self,
        pos: Position,
        action: str,
        data: dict
    ) -> None:
        # Create operation
        self.clock += 1
        op = TileOperation(
            op_id=uuid.uuid4(),
            timestamp=self.clock,
            user_id=self.user_id,
            position=pos,
            action=action,
            data=data
        )

        # Apply locally (optimistic)
        self._apply_operation(op)

        # Send to server
        self.pending.append(op)
        await self.ws.send(json.dumps(asdict(op)))

    async def _receive_loop(self) -> None:
        while True:
            msg = await self.ws.recv()
            op = TileOperation(**json.loads(msg))

            # Update clock (Lamport algorithm)
            self.clock = max(self.clock, op.timestamp) + 1

            # Apply operation
            self._apply_operation(op)

            # Remove from pending if it's ours
            self.pending = [p for p in self.pending if p.op_id != op.op_id]

    def _apply_operation(self, op: TileOperation) -> None:
        # Insert operation in sorted order (CRDT)
        bisect.insort(self.operations, op)

        # Recompute tile state
        tile = self._compute_tile_state(op.position)
        self.game_map.set_tile(op.position, tile)
```

**B) Server Broadcast Manager**
```python
# server/broadcast_manager.py
class BroadcastManager:
    def __init__(self):
        self.clients: list[WebSocket] = []
        self.operations: list[TileOperation] = []

    async def handle_client(self, ws: WebSocket) -> None:
        self.clients.append(ws)
        try:
            # Send current state
            await ws.send(json.dumps({
                "type": "initial_state",
                "operations": [asdict(op) for op in self.operations]
            }))

            # Receive loop
            async for msg in ws:
                op = TileOperation(**json.loads(msg))

                # Store operation
                bisect.insort(self.operations, op)

                # Broadcast to all clients
                await self.broadcast(op)
        finally:
            self.clients.remove(ws)

    async def broadcast(self, op: TileOperation) -> None:
        msg = json.dumps(asdict(op))
        await asyncio.gather(
            *[client.send(msg) for client in self.clients]
        )
```

**C) Conflict Resolution**
```python
# Conflicts resolved by CRDT total order
# Example: Two users paint same tile simultaneously

# User A: timestamp=100, op_id=UUID("aaa...")
# User B: timestamp=100, op_id=UUID("bbb...")

# If UUID("aaa...") < UUID("bbb..."):
#     User A's operation wins
# else:
#     User B's operation wins

# All clients converge to same state!
```

**Deliverable:** Component specs + sequence diagrams

### 4. ELABORATE (4h) - Implementation Plan

**Milestones:**

**M1: Local CRDT Implementation (8h)**
- TileOperation dataclass
- LWWTileSet
- Lamport clock
- Tests

**M2: Network Protocol (10h)**
- WebSocket client
- WebSocket server
- Serialization
- Tests

**M3: Synchronization Manager (12h)**
- SyncManager
- Optimistic updates
- Rollback on conflicts
- Tests

**M4: Server Persistence (6h)**
- Save operations to SQLite
- Load on reconnect
- Garbage collection (old ops)
- Tests

**M5: UI Integration (8h)**
- Connect button
- User list widget
- Cursor tracking (show other users)
- Tests

**Total:** ~44 hours (2 weeks sprint)

**Deliverable:** Project plan with Gantt chart

### 5. PROTOTYPE (8h) - Proof of Concept

**Build minimal prototype:**
```python
# prototype/live_demo.py
import asyncio
import websockets

# Simple echo server
async def echo_server(ws, path):
    async for msg in ws:
        # Broadcast to all clients
        await ws.send(msg)

# Start server
start_server = websockets.serve(echo_server, "localhost", 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
```

**Client test:**
```python
# Connect two clients, send operations, verify sync
```

**Deliverable:** Working demo video

### 6. PLAN (4h) - Handoff Document

**Create comprehensive handoff for Sonnet:**
```markdown
# Live Collaboration Implementation Handoff

## Overview
Implement CRDT-based live collaboration system.

## Architecture
[Include all diagrams from step 3]

## Implementation Order
1. M1: TileOperation + LWWTileSet (Sonnet, 8h)
2. M2: WebSocket protocol (Sonnet, 10h)
3. M3: SyncManager (Sonnet, 12h)
4. M4: Server (Sonnet, 6h)
5. M5: UI (Sonnet, 8h)

## Code Templates
[Include all starter code]

## Testing Strategy
[Include test scenarios]

## Performance Targets
- Latency: <200ms
- Bandwidth: <100 KB/s per user
- Scalability: 10 concurrent users

## References
- CRDT Paper: https://hal.inria.fr/inria-00555588
- Figma Architecture: https://www.figma.com/blog/how-figmas-multiplayer-technology-works/
```

**Deliverable:** Complete handoff doc

### 7. DELEGATE - Assign to Sonnet

```bash
@sonnet: Implement live collaboration system

Handoff: docs/handoff/live_collaboration.md
Priority: High
Complexity: Very High
Estimated: 44 hours (2 weeks)
```

### 8. EVALUATE - Post-Implementation

**Validation:**
- [ ] Two clients can edit simultaneously
- [ ] Operations converge to same state
- [ ] Undo/redo works correctly
- [ ] Performance meets targets
- [ ] Tests pass (100% coverage)
- [ ] Security audit passed

**Deliverable:** Evaluation report

## Quality Gates
- âœ… CRDT convergence proven
- âœ… Performance benchmarks met
- âœ… Security audit passed
- âœ… Documentation complete
- âœ… Demo video created

## References
- CRDTs: https://crdt.tech/
- Figma Multiplayer: https://www.figma.com/blog/how-figmas-multiplayer-technology-works/
- WebSockets: https://websockets.readthedocs.io/
```

---

# Workflows Especializados

## Gemini 3 - Prototyping & Research

### `.gemini/workflows/validate-algorithm.md`

```markdown
---
description: Rapid algorithm validation and comparison
duration: 45-60 minutes
---

## Steps

### 1. UNDERSTAND (15min)
- What is the algorithm?
- What is INPUT/OUTPUT?
- What is the performance target?

### 2. IMPLEMENT (20min)
**Create throwaway prototype:**
```python
# prototype_border_algorithm.py
# Quick and dirty - doesn't need to be production-quality

def compute_border_mask_v1(neighbors):
    # Naive approach
    mask = 0
    for i, n in enumerate(neighbors):
        if n == "grass":
            mask |= (1 << i)
    return mask

def compute_border_mask_v2(neighbors):
    # Optimized approach
    lookup = {"grass": True, "dirt": False}
    return sum((1 << i) for i, n in enumerate(neighbors) if lookup.get(n, False))
```

### 3. BENCHMARK (10min)
```python
import timeit

# Test data
neighbors = ["grass", "dirt", "grass"] * 1000

# V1
time_v1 = timeit.timeit(
    lambda: compute_border_mask_v1(neighbors),
    number=10000
)

# V2
time_v2 = timeit.timeit(
    lambda: compute_border_mask_v2(neighbors),
    number=10000
)

print(f"V1: {time_v1:.4f}s")
print(f"V2: {time_v2:.4f}s")
print(f"Speedup: {time_v1/time_v2:.2f}x")
```

### 4. DOCUMENT (10min)
**Create report:**
```markdown
# Border Algorithm Validation Report

## Tested Algorithms
- V1: Naive loop
- V2: List comprehension

## Results
- V1: 2.34ms
- V2: 1.12ms
- Speedup: 2.09x

## Recommendation
Use V2 for production (faster + cleaner code)

## Next Steps
- Implement in production (assign to Sonnet)
- Add tests
- Integrate with BrushManager
```

### 5. HANDOFF (5min)
```bash
@sonnet: Implement border mask algorithm (use V2 from report)

Report: prototype/border_algorithm_report.md
Priority: Medium
Estimated: 2 hours
```

## Output
- Prototype code (throwaway)
- Benchmark results
- Recommendation report
```

---

# Rules Avançadas

## `.agent/rules/security.md`

```markdown
# Security Rules - py_rme_canary

## Input Validation (CRITICAL)

### File Paths
```python
from pathlib import Path

def validate_path(path: Path) -> Path:
    \"\"\"Validate file path against directory traversal.\"\"\"
    resolved = path.resolve()

    # Check against allowed directories
    allowed_dirs = [
        Path("maps/"),
        Path("data/"),
    ]

    if not any(resolved.is_relative_to(d) for d in allowed_dirs):
        raise SecurityError(f"Path {path} not allowed")

    return resolved

# Usage
user_path = Path(request.args["path"])
safe_path = validate_path(user_path)
```

### File Size Limits
```python
# Use MemoryGuard
from py_rme_canary.core.memory_guard import MemoryGuard

guard = MemoryGuard.get_instance()

def load_file(path: Path) -> bytes:
    size = path.stat().st_size

    if not guard.can_allocate(size):
        raise MemoryError(f"File too large: {size} bytes")

    with guard.track_allocation(size):
        return path.read_bytes()
```

### User Input Sanitization
```python
import re

def sanitize_map_name(name: str) -> str:
    \"\"\"Sanitize user-provided map name.\"\"\"
    # Allow only alphanumeric + underscore + dash
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ValueError(f"Invalid map name: {name}")

    # Limit length
    if len(name) > 100:
        raise ValueError("Map name too long")

    return name
```

## Atomic Operations

### Atomic File Writes
```python
import tempfile
import shutil

def atomic_write(path: Path, data: bytes) -> None:
    \"\"\"Write file atomically (prevents corruption on crash).\"\"\"
    # Write to temp file first
    temp_path = path.with_suffix(".tmp")
    temp_path.write_bytes(data)

    # Atomic rename (POSIX guarantees atomicity)
    temp_path.replace(path)
```

## Cryptographic Security

### Secure Random Generation
```python
import secrets

# NEVER use random.random() for security
# ALWAYS use secrets module

def generate_session_token() -> str:
    return secrets.token_urlsafe(32)
```

## Audit Logging
```python
import logging

# Log all security-relevant events
security_logger = logging.getLogger("security")

def load_map(path: Path, user_id: str) -> GameMap:
    security_logger.info(
        f"User {user_id} loading map {path}",
        extra={"user_id": user_id, "path": str(path)}
    )

    # ... load map
```

## Quality Gates
- âœ… All user inputs validated
- âœ… File size limits enforced
- âœ… Atomic writes for saves
- âœ… Security audit passed (bandit)
- âœ… No secrets in code

## References
- OWASP: https://owasp.org/www-project-top-ten/
- Python Security: https://python.readthedocs.io/en/stable/library/security_warnings.html
```

---

## 🎯 Summary

Este sistema fornece:

1. **Cursor IDE** (.cursor/)
   - 2 rules files (RME core + TFS/Canary)
   - 7 slash commands
   - Otimizado para GPT-Codex

2. **Antigravity** (.agent/, .anthropic/)
   - Workflows especializados (TFS port, Canary protocol)
   - Rules avançadas (OTBM, performance, security)
   - Integração multi-LLM

3. **Workflows Especializados**
   - OTBM parsing
   - Brush implementation
   - Live collaboration
   - Algorithm validation

4. **Context Profundo**
   - RME C++ patterns
   - TFS/Canary specifics
   - Performance optimization
   - Security best practices

**Próximos Passos:**
1. Execute `install_multi_ide_setup.py`
2. Teste comandos no Cursor
3. Valide workflows no Antigravity
4. Customize para seu projeto
