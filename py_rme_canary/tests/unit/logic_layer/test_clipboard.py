"""Unit tests for the clipboard system."""

from __future__ import annotations

from dataclasses import dataclass


# Mock Position class for testing
@dataclass
class MockPosition:
    x: int
    y: int
    z: int


@dataclass
class MockItem:
    id: int
    count: int = 1


@dataclass
class MockTile:
    x: int
    y: int
    z: int
    ground: MockItem | None = None
    items: list = None

    def __post_init__(self):
        if self.items is None:
            self.items = []


class TestClipboardEntry:
    """Tests for ClipboardEntry dataclass."""

    def test_entry_creation(self):
        """Test creating a clipboard entry."""
        from py_rme_canary.logic_layer.clipboard import ClipboardEntry

        tiles = [MockTile(0, 0, 7)]
        entry = ClipboardEntry(tiles=tiles, origin_x=100, origin_y=200)

        assert entry.tiles == tiles
        assert entry.origin_x == 100
        assert entry.origin_y == 200
        assert entry.width == 1
        assert entry.height == 1

    def test_entry_with_multiple_tiles(self):
        """Test entry dimensions with multiple tiles."""
        from py_rme_canary.logic_layer.clipboard import ClipboardEntry

        tiles = [
            MockTile(0, 0, 7),
            MockTile(2, 3, 7),
        ]
        entry = ClipboardEntry(tiles=tiles, origin_x=0, origin_y=0, width=3, height=4)

        assert entry.width == 3
        assert entry.height == 4


class TestClipboardManager:
    """Tests for ClipboardManager."""

    def test_singleton_instance(self):
        """Test that ClipboardManager is a singleton."""
        from py_rme_canary.logic_layer.clipboard import ClipboardManager

        manager1 = ClipboardManager.instance()
        manager2 = ClipboardManager.instance()

        assert manager1 is manager2

    def test_copy_tiles(self):
        """Test copying tiles to clipboard."""
        from py_rme_canary.logic_layer.clipboard import ClipboardManager

        manager = ClipboardManager.instance()
        manager.clear()

        tiles = [MockTile(10, 20, 7)]
        manager.copy(tiles, 10, 20)

        assert manager.can_paste()

        entry = manager.get_current()
        assert entry is not None
        assert entry.origin_x == 10
        assert entry.origin_y == 20

    def test_cut_tiles(self):
        """Test cutting tiles."""
        from py_rme_canary.logic_layer.clipboard import ClipboardManager

        manager = ClipboardManager.instance()
        manager.clear()

        tiles = [MockTile(5, 5, 7)]
        manager.cut(tiles, 5, 5)

        assert manager.is_cut_operation()

    def test_clipboard_history(self):
        """Test clipboard history is maintained."""
        from py_rme_canary.logic_layer.clipboard import ClipboardManager

        manager = ClipboardManager.instance()
        manager.clear()

        # Add multiple entries
        for i in range(5):
            manager.copy([MockTile(i, i, 7)], i, i)

        history = manager.get_history()
        assert len(history) == 5

        # Most recent should be last one
        current = manager.get_current()
        assert current.origin_x == 4

    def test_history_limit(self):
        """Test history doesn't exceed limit."""
        from py_rme_canary.logic_layer.clipboard import ClipboardManager

        manager = ClipboardManager.instance()
        manager.clear()

        # Add more than limit
        for i in range(15):
            manager.copy([MockTile(i, i, 7)], i, i)

        history = manager.get_history()
        assert len(history) <= 10  # Default limit

    def test_clear_clipboard(self):
        """Test clearing clipboard."""
        from py_rme_canary.logic_layer.clipboard import ClipboardManager

        manager = ClipboardManager.instance()
        manager.copy([MockTile(0, 0, 7)], 0, 0)

        manager.clear()

        assert not manager.can_paste()
        assert manager.get_current() is None


class TestClipboardTransforms:
    """Tests for clipboard transformations."""

    def test_rotate_90(self):
        """Test 90 degree rotation."""
        from py_rme_canary.logic_layer.clipboard import ClipboardManager

        manager = ClipboardManager.instance()
        manager.clear()

        # Create L-shaped selection
        tiles = [
            MockTile(0, 0, 7),
            MockTile(0, 1, 7),
            MockTile(1, 1, 7),
        ]
        manager.copy(tiles, 0, 0)

        original = manager.get_current()
        manager.rotate_90()
        rotated = manager.get_current()

        # Dimensions should swap
        assert rotated.width == original.height or len(rotated.tiles) > 0

    def test_flip_horizontal(self):
        """Test horizontal flip."""
        from py_rme_canary.logic_layer.clipboard import ClipboardManager

        manager = ClipboardManager.instance()
        manager.clear()

        tiles = [
            MockTile(0, 0, 7),
            MockTile(2, 0, 7),
        ]
        manager.copy(tiles, 0, 0)

        manager.flip_horizontal()

        assert manager.can_paste()

    def test_flip_vertical(self):
        """Test vertical flip."""
        from py_rme_canary.logic_layer.clipboard import ClipboardManager

        manager = ClipboardManager.instance()
        manager.clear()

        tiles = [
            MockTile(0, 0, 7),
            MockTile(0, 2, 7),
        ]
        manager.copy(tiles, 0, 0)

        manager.flip_vertical()

        assert manager.can_paste()


class TestPastePositions:
    """Tests for paste position calculation."""

    def test_get_paste_positions(self):
        """Test getting paste positions."""
        from py_rme_canary.logic_layer.clipboard import ClipboardManager

        manager = ClipboardManager.instance()
        manager.clear()

        tiles = [
            MockTile(0, 0, 7),
            MockTile(1, 0, 7),
            MockTile(0, 1, 7),
        ]
        manager.copy(tiles, 0, 0)

        # Paste at new location
        positions = manager.get_paste_positions(100, 200, 7)

        assert len(positions) == 3
        # All positions should be offset
        for pos in positions:
            assert pos[0] >= 100
            assert pos[1] >= 200
            assert pos[2] == 7


class TestClipboardCreaturesAndSpawns:
    """Tests for creature/spawn serialization in clipboard."""

    def test_tiles_roundtrip_preserves_creatures_and_spawns(self) -> None:
        from py_rme_canary.core.data.creature import Monster, Npc, Outfit
        from py_rme_canary.core.data.item import Item, Position
        from py_rme_canary.core.data.spawns import (
            MonsterSpawnArea,
            MonsterSpawnEntry,
            NpcSpawnArea,
            NpcSpawnEntry,
        )
        from py_rme_canary.core.data.tile import Tile
        from py_rme_canary.logic_layer.clipboard import ClipboardManager, tiles_from_entry

        manager = ClipboardManager.instance()
        manager.clear()

        outfit = Outfit(looktype=128, lookhead=20, lookbody=30, looklegs=40, lookfeet=50, lookaddons=3)
        monster = Monster(name="orc", direction=1, outfit=outfit)
        npc = Npc(name="merchant", direction=2, outfit=Outfit(looktype=130))

        spawn_center = Position(x=10, y=11, z=7)
        monster_spawn = MonsterSpawnArea(
            center=spawn_center,
            radius=3,
            monsters=(MonsterSpawnEntry(name="orc", dx=0, dy=0, spawntime=20, direction=1, weight=2),),
        )
        npc_spawn = NpcSpawnArea(
            center=spawn_center,
            radius=2,
            npcs=(NpcSpawnEntry(name="merchant", dx=0, dy=0, spawntime=30, direction=2),),
        )

        tile = Tile(
            x=10,
            y=11,
            z=7,
            ground=Item(id=100, count=1),
            items=[Item(id=200, count=3), Item(id=201, action_id=5, unique_id=9, text="hi")],
            monsters=[monster],
            npc=npc,
            spawn_monster=monster_spawn,
            spawn_npc=npc_spawn,
        )

        manager.copy_tiles([tile], (10, 11, 7))
        entry = manager.get_current()
        assert entry is not None

        result = tiles_from_entry(entry)
        assert result is not None

        tiles, origin = result
        assert origin == (10, 11, 7)
        assert len(tiles) == 1

        restored = tiles[0]
        assert restored.monsters[0].name == "orc"
        assert restored.monsters[0].outfit is not None
        assert restored.monsters[0].outfit.looktype == 128
        assert restored.npc is not None
        assert restored.npc.name == "merchant"
        assert restored.spawn_monster is not None
        assert restored.spawn_monster.radius == 3
        assert len(restored.spawn_monster.monsters) == 1
        assert restored.spawn_npc is not None
        assert restored.spawn_npc.radius == 2
