"""Script Automation Engine.

This module provides a sandboxed scripting environment for map automation.
Users can write Python scripts to perform batch operations on maps.

Reference:
    - Similar to scripting in Tiled, RPG Maker, Unity
    - Extensibility for power users

Features:
    - ScriptEngine: Execute Python scripts in sandboxed environment
    - MapAPI: Safe API for scripts to interact with maps
    - ScriptResult: Execution results and logging
    - Built-in utility functions for common operations

Layer: logic_layer (no PyQt6 dependencies)
"""

from __future__ import annotations

import ast
import logging
import time
import traceback
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field, replace
from enum import Enum, auto
from io import StringIO
from typing import TYPE_CHECKING, Any

from py_rme_canary.core.data.item import Item

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.tile import Tile

logger = logging.getLogger(__name__)


# Position type alias
Position = tuple[int, int, int]  # (x, y, z)


class ScriptStatus(Enum):
    """Status of script execution."""

    SUCCESS = auto()
    ERROR = auto()
    TIMEOUT = auto()
    CANCELLED = auto()
    SYNTAX_ERROR = auto()
    SECURITY_ERROR = auto()


@dataclass
class ScriptResult:
    """Result of script execution.

    Attributes:
        status: Execution status.
        output: Script output (print statements).
        error: Error message if any.
        return_value: Value returned by script.
        execution_time: Time taken in seconds.
        tiles_modified: Number of tiles modified.
        items_added: Number of items added.
        items_removed: Number of items removed.
    """

    status: ScriptStatus = ScriptStatus.SUCCESS
    output: str = ""
    error: str = ""
    return_value: Any = None
    execution_time: float = 0.0
    tiles_modified: int = 0
    items_added: int = 0
    items_removed: int = 0

    @property
    def success(self) -> bool:
        return self.status == ScriptStatus.SUCCESS

    def summary(self) -> str:
        """Generate execution summary."""
        lines = [
            f"Status: {self.status.name}",
            f"Time: {self.execution_time:.3f}s",
            f"Tiles Modified: {self.tiles_modified}",
            f"Items: +{self.items_added}, -{self.items_removed}",
        ]
        if self.error:
            lines.append(f"Error: {self.error}")
        return "\n".join(lines)


@dataclass
class ScriptConfig:
    """Configuration for script execution.

    Attributes:
        timeout_seconds: Maximum execution time.
        max_iterations: Maximum loop iterations.
        allow_file_access: Whether to allow file operations.
        allow_imports: List of allowed import modules.
        dry_run: If True, don't apply changes to map.
    """

    timeout_seconds: float = 30.0
    max_iterations: int = 1000000
    allow_file_access: bool = False
    allow_imports: list[str] = field(default_factory=lambda: ["math", "random", "itertools", "functools"])
    dry_run: bool = False


class MapAPI:
    """Safe API for scripts to interact with maps.

    Provides a restricted interface to map data to prevent
    dangerous operations in user scripts.

    Example in script:
        # Get tile
        tile = map.get_tile(100, 100, 7)

        # Modify tile
        map.set_ground(100, 100, 7, 4526)

        # Add item
        map.add_item(100, 100, 7, 2120)

        # Iterate region
        for tile in map.iter_region(100, 100, 110, 110, 7):
            if tile.has_item(2120):
                map.remove_item(tile.x, tile.y, tile.z, 2120)
    """

    def __init__(self, game_map: GameMap, config: ScriptConfig) -> None:
        """Initialize the Map API.

        Args:
            game_map: The map to operate on.
            config: Script configuration.
        """
        self._map = game_map
        self._config = config
        self._stats = {
            "tiles_modified": 0,
            "items_added": 0,
            "items_removed": 0,
        }
        self._pending_changes: list[dict[str, Any]] = []

    @property
    def width(self) -> int:
        """Map width in tiles."""
        return self._map.header.width

    @property
    def height(self) -> int:
        """Map height in tiles."""
        return self._map.header.height

    @property
    def stats(self) -> dict[str, int]:
        """Get current operation statistics."""
        return self._stats.copy()

    def get_tile(self, x: int, y: int, z: int) -> TileProxy | None:
        """Get a tile at position.

        Args:
            x: X coordinate.
            y: Y coordinate.
            z: Floor level.

        Returns:
            TileProxy wrapper or None if tile doesn't exist.
        """
        tile = self._map.get_tile(x, y, z)
        if tile is None:
            return None
        return TileProxy(tile, x, y, z)

    def create_tile(self, x: int, y: int, z: int) -> TileProxy:
        """Create a tile at position (or get existing).

        Args:
            x: X coordinate.
            y: Y coordinate.
            z: Floor level.

        Returns:
            TileProxy wrapper.
        """
        tile = self._map.get_tile(x, y, z)
        if tile is None:
            tile = self._map.ensure_tile(x, y, z)
        return TileProxy(tile, x, y, z)

    def tile_exists(self, x: int, y: int, z: int) -> bool:
        """Check if tile exists."""
        return self._map.get_tile(x, y, z) is not None

    def set_ground(self, x: int, y: int, z: int, item_id: int) -> bool:
        """Set ground item at position.

        Args:
            x: X coordinate.
            y: Y coordinate.
            z: Floor level.
            item_id: Ground item ID.

        Returns:
            True if successful.
        """
        if self._config.dry_run:
            self._pending_changes.append(
                {
                    "type": "set_ground",
                    "pos": (x, y, z),
                    "item_id": item_id,
                }
            )
        else:
            tile = self._map.get_tile(x, y, z)
            if tile is None:
                tile = self._map.ensure_tile(x, y, z)

            # Create item and set as ground
            if hasattr(self._map, "item_factory"):
                item = self._map.item_factory.create(item_id)
            else:
                # Basic fallback
                item = Item(id=item_id)

            new_tile = tile.with_ground(item)
            self._map.set_tile(new_tile)

        self._stats["tiles_modified"] += 1
        return True

    def add_item(self, x: int, y: int, z: int, item_id: int, count: int = 1) -> bool:
        """Add an item to a tile.

        Args:
            x: X coordinate.
            y: Y coordinate.
            z: Floor level.
            item_id: Item ID.
            count: Stack count.

        Returns:
            True if successful.
        """
        if self._config.dry_run:
            self._pending_changes.append(
                {
                    "type": "add_item",
                    "pos": (x, y, z),
                    "item_id": item_id,
                    "count": count,
                }
            )
        else:
            tile = self._map.get_tile(x, y, z)
            if tile is None:
                tile = self._map.ensure_tile(x, y, z)

            if hasattr(self._map, "item_factory"):
                item = self._map.item_factory.create(item_id)
            else:
                item = Item(id=item_id)

            if hasattr(item, "count"):
                item.count = count

            new_tile = tile.add_item(item)
            self._map.set_tile(new_tile)

        self._stats["items_added"] += 1
        self._stats["tiles_modified"] += 1
        return True

    def remove_item(self, x: int, y: int, z: int, item_id: int, all_instances: bool = False) -> int:
        """Remove item(s) from a tile.

        Args:
            x: X coordinate.
            y: Y coordinate.
            z: Floor level.
            item_id: Item ID to remove.
            all_instances: Remove all matching items.

        Returns:
            Number of items removed.
        """
        if self._config.dry_run:
            self._pending_changes.append(
                {
                    "type": "remove_item",
                    "pos": (x, y, z),
                    "item_id": item_id,
                    "all": all_instances,
                }
            )
            return 1

        tile = self._map.get_tile(x, y, z)
        if tile is None:
            return 0

        removed = 0
        new_items = []
        found_removal = False

        for item in tile.items:
            should_remove = False
            if not found_removal or all_instances:
                if item.id == item_id:
                    should_remove = True
                    removed += 1
                    found_removal = True

            if not should_remove:
                new_items.append(item)

        if removed > 0:
            new_tile = replace(tile, items=new_items, modified=True)
            self._map.set_tile(new_tile)
            self._stats["tiles_modified"] += 1

        self._stats["items_removed"] += removed
        return removed

    def clear_tile(self, x: int, y: int, z: int, keep_ground: bool = False) -> int:
        """Clear all items from a tile.

        Args:
            x: X coordinate.
            y: Y coordinate.
            z: Floor level.
            keep_ground: Keep ground item.

        Returns:
            Number of items removed.
        """
        if self._config.dry_run:
            self._pending_changes.append(
                {
                    "type": "clear_tile",
                    "pos": (x, y, z),
                    "keep_ground": keep_ground,
                }
            )
            return 1

        tile = self._map.get_tile(x, y, z)
        if tile is None:
            return 0

        removed = len(list(tile.items))
        new_ground = tile.ground

        # Clear ground if requested
        if not keep_ground and tile.ground:
            new_ground = None
            removed += 1

        if removed > 0:
            new_tile = replace(tile, items=[], ground=new_ground, modified=True)
            self._map.set_tile(new_tile)
            self._stats["tiles_modified"] += 1

        self._stats["items_removed"] += removed
        return removed

    def iter_region(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        z: int,
    ) -> Iterator[TileProxy]:
        """Iterate over tiles in a rectangular region.

        Args:
            x1: Start X.
            y1: Start Y.
            x2: End X.
            y2: End Y.
            z: Floor level.

        Yields:
            TileProxy for each existing tile in region.
        """
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)

        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                tile = self._map.get_tile(x, y, z)
                if tile is not None:
                    yield TileProxy(tile, x, y, z)

    def iter_floor(self, z: int) -> Iterator[TileProxy]:
        """Iterate over all tiles on a floor.

        Args:
            z: Floor level.

        Yields:
            TileProxy for each existing tile.
        """
        for y in range(self._map.header.height):
            for x in range(self._map.header.width):
                tile = self._map.get_tile(x, y, z)
                if tile is not None:
                    yield TileProxy(tile, x, y, z)

    def find_items(self, item_id: int, floor: int | None = None) -> list[Position]:
        """Find all positions with a specific item.

        Args:
            item_id: Item ID to search for.
            floor: Optional floor to limit search.

        Returns:
            List of positions containing the item.
        """
        positions: list[Position] = []
        floors = [floor] if floor is not None else range(16)

        for z in floors:
            for y in range(self._map.header.height):
                for x in range(self._map.header.width):
                    tile = self._map.get_tile(x, y, z)
                    if tile is None:
                        continue

                    # Check ground
                    if tile.ground and tile.ground.id == item_id:
                        positions.append((x, y, z))
                        continue

                    # Check items
                    for item in tile.items:
                        if item.id == item_id:
                            positions.append((x, y, z))
                            break

        return positions

    def replace_item(
        self,
        old_id: int,
        new_id: int,
        floor: int | None = None,
    ) -> int:
        """Replace all instances of an item with another.

        Args:
            old_id: Item ID to replace.
            new_id: New item ID.
            floor: Optional floor to limit replacement.

        Returns:
            Number of items replaced.
        """
        positions = self.find_items(old_id, floor)
        count = 0

        for x, y, z in positions:
            self.remove_item(x, y, z, old_id, all_instances=True)
            self.add_item(x, y, z, new_id)
            count += 1

        return count

    def log(self, message: str) -> None:
        """Log a message (appears in script output)."""
        print(message)


@dataclass(slots=True)
class TileProxy:
    """Safe wrapper around Tile for script access."""

    _tile: Tile
    x: int
    y: int
    z: int

    @property
    def ground_id(self) -> int:
        """Ground item ID or 0."""
        if self._tile.ground:
            return self._tile.ground.id
        return 0

    @property
    def item_count(self) -> int:
        """Number of items (excluding ground)."""
        return len(list(self._tile.items))

    @property
    def item_ids(self) -> list[int]:
        """List of item IDs on tile."""
        return [item.id for item in self._tile.items]

    @property
    def house_id(self) -> int:
        """House ID or 0."""
        return getattr(self._tile, "house_id", 0) or 0

    def has_item(self, item_id: int) -> bool:
        """Check if tile has specific item."""
        if self._tile.ground and self._tile.ground.id == item_id:
            return True
        return any(item.id == item_id for item in self._tile.items)

    def has_ground(self) -> bool:
        """Check if tile has ground."""
        return self._tile.ground is not None

    @property
    def position(self) -> Position:
        """Get position tuple."""
        return (self.x, self.y, self.z)


# Forbidden AST nodes for security
FORBIDDEN_AST_NODES = {
    ast.Import,
    ast.ImportFrom,
    ast.Global,
    ast.Nonlocal,
    ast.AsyncFunctionDef,
    ast.AsyncFor,
    ast.AsyncWith,
    ast.Await,
}


class ScriptSecurityChecker(ast.NodeVisitor):
    """AST visitor to check for dangerous operations."""

    def __init__(self, allowed_imports: list[str]) -> None:
        self.allowed_imports = set(allowed_imports)
        self.errors: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name.split(".")[0] not in self.allowed_imports:
                self.errors.append(f"Import not allowed: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            base_module = node.module.split(".")[0]
            if base_module not in self.allowed_imports:
                self.errors.append(f"Import not allowed: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Check for dangerous built-in calls
        if isinstance(node.func, ast.Name):
            name = node.func.id
            dangerous = {
                "eval",
                "exec",
                "compile",
                "open",
                "__import__",
                "getattr",
                "setattr",
                "delattr",
                "format",
            }
            if name in dangerous:
                self.errors.append(f"Forbidden function: {name}")

        # Check for dangerous method calls (e.g. "".format())
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("format", "format_map"):
            self.errors.append(f"Forbidden method: {node.func.attr}")

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Check for dangerous attribute access
        dangerous_attrs = {
            "__class__",
            "__base__",
            "__bases__",
            "__subclasses__",
            "__code__",
            "__closure__",
            "__globals__",
            "__dict__",
            "__module__",
            "__mro__",
            "__getattribute__",
            "__func__",
            "__self__",
            "__traceback__",
            "__context__",
            "__cause__",
            "gi_frame",
            "gi_code",
            "gi_yieldfrom",
            "cr_frame",
            "cr_code",
            "cr_origin",
            "ag_frame",
            "ag_code",
            "f_back",
            "f_builtins",
            "f_code",
            "f_globals",
            "f_locals",
            "f_trace",
            "tb_frame",
            "tb_next",
        }
        if node.attr in dangerous_attrs:
            self.errors.append(f"Forbidden attribute access: {node.attr}")
        self.generic_visit(node)


class ScriptEngine:
    """Engine for executing automation scripts.

    Example:
        engine = ScriptEngine(game_map)

        script = '''
        # Replace all items 100 with item 200 on floor 7
        count = map.replace_item(100, 200, floor=7)
        map.log(f"Replaced {count} items")
        '''

        result = engine.execute(script)
        print(result.summary())
    """

    def __init__(self, game_map: GameMap | None = None) -> None:
        """Initialize the script engine.

        Args:
            game_map: Map for scripts to operate on.
        """
        self._map = game_map
        self._config = ScriptConfig()
        self._on_progress: Callable[[str, float], None] | None = None

    def set_map(self, game_map: GameMap) -> None:
        """Set the map for script operations."""
        self._map = game_map

    def set_config(self, config: ScriptConfig) -> None:
        """Set script configuration."""
        self._config = config

    def set_progress_callback(self, callback: Callable[[str, float], None]) -> None:
        """Set callback for progress updates."""
        self._on_progress = callback

    def validate_script(self, script: str) -> tuple[bool, str]:
        """Validate a script without executing it.

        Args:
            script: Python script code.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            tree = ast.parse(script)
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"

        checker = ScriptSecurityChecker(self._config.allow_imports)
        checker.visit(tree)

        if checker.errors:
            return False, "; ".join(checker.errors)

        return True, ""

    def execute(self, script: str) -> ScriptResult:
        """Execute a script.

        Args:
            script: Python script code.

        Returns:
            ScriptResult with execution details.
        """
        if self._map is None:
            return ScriptResult(
                status=ScriptStatus.ERROR,
                error="No map set for script execution",
            )

        # Validate script
        is_valid, error = self.validate_script(script)
        if not is_valid:
            is_security = "not allowed" in error or "Forbidden" in error
            return ScriptResult(
                status=ScriptStatus.SECURITY_ERROR if is_security else ScriptStatus.SYNTAX_ERROR,
                error=error,
            )

        # Setup execution environment
        output = StringIO()
        map_api = MapAPI(self._map, self._config)

        def safe_import(
            name: str,
            globals: dict[str, Any] | None = None,
            locals: dict[str, Any] | None = None,
            fromlist: tuple[str, ...] = (),
            level: int = 0,
        ) -> Any:
            base_name = name.split(".")[0]
            if base_name in self._config.allow_imports:
                return __import__(name, globals, locals, fromlist, level)
            raise ImportError(f"Import not allowed: {name}")

        # Build safe globals
        safe_builtins = {
            "__import__": safe_import,
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "frozenset": frozenset,
            "int": int,
            "len": len,
            "list": list,
            "map": map,  # Python's map function
            "max": max,
            "min": min,
            "print": lambda *args, **kwargs: print(*args, file=output, **kwargs),
            "range": range,
            "reversed": reversed,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "zip": zip,
            "True": True,
            "False": False,
            "None": None,
        }

        # Import allowed modules
        for module_name in self._config.allow_imports:
            try:
                module = __import__(module_name)
                safe_builtins[module_name] = module
            except ImportError:
                pass

        script_globals = {
            "__builtins__": safe_builtins,
            "map": map_api,  # Our MapAPI, shadowing Python's map
            "Map": map_api,  # Alternative name
        }

        # Execute with timeout tracking
        start_time = time.time()
        result = ScriptResult()

        try:
            # Executing user script in restricted environment (B102 suppressed: sandbox design)
            exec(compile(script, "<script>", "exec"), script_globals)  # nosec B102

            result.status = ScriptStatus.SUCCESS
            result.return_value = script_globals.get("result")

        except TimeoutError:
            result.status = ScriptStatus.TIMEOUT
            result.error = f"Script exceeded {self._config.timeout_seconds}s timeout"

        except Exception as e:
            result.status = ScriptStatus.ERROR
            result.error = f"{type(e).__name__}: {str(e)}"

            # Include traceback for debugging
            tb = traceback.format_exc()
            output.write(f"\n--- Traceback ---\n{tb}")

        finally:
            result.execution_time = time.time() - start_time
            result.output = output.getvalue()

            # Get stats from API
            stats = map_api.stats
            result.tiles_modified = stats["tiles_modified"]
            result.items_added = stats["items_added"]
            result.items_removed = stats["items_removed"]

        return result

    def execute_file(self, path: str) -> ScriptResult:
        """Execute a script from file.

        Args:
            path: Path to script file.

        Returns:
            ScriptResult with execution details.
        """
        try:
            with open(path, encoding="utf-8") as f:
                script = f.read()
        except Exception as e:
            return ScriptResult(
                status=ScriptStatus.ERROR,
                error=f"Failed to read script file: {e}",
            )

        return self.execute(script)


def create_script_engine(game_map: GameMap | None = None) -> ScriptEngine:
    """Factory function to create a ScriptEngine.

    Args:
        game_map: Optional map for operations.

    Returns:
        Configured ScriptEngine.
    """
    return ScriptEngine(game_map)


# Built-in script templates
SCRIPT_TEMPLATES = {
    "replace_item": """
# Replace all instances of an item
OLD_ID = {old_id}
NEW_ID = {new_id}
FLOOR = {floor}  # or None for all floors

count = Map.replace_item(OLD_ID, NEW_ID, floor=FLOOR)
Map.log(f"Replaced {{count}} items")
""",
    "clear_region": """
# Clear all items in a region
X1, Y1 = {x1}, {y1}
X2, Y2 = {x2}, {y2}
FLOOR = {floor}
KEEP_GROUND = True

count = 0
for tile in Map.iter_region(X1, Y1, X2, Y2, FLOOR):
    count += Map.clear_tile(tile.x, tile.y, tile.z, keep_ground=KEEP_GROUND)

Map.log(f"Cleared {{count}} items")
""",
    "fill_border": """
# Fill border of a region with an item
X1, Y1 = {x1}, {y1}
X2, Y2 = {x2}, {y2}
FLOOR = {floor}
ITEM_ID = {item_id}

count = 0
for x in range(X1, X2 + 1):
    for y in [Y1, Y2]:
        Map.add_item(x, y, FLOOR, ITEM_ID)
        count += 1

for y in range(Y1 + 1, Y2):
    for x in [X1, X2]:
        Map.add_item(x, y, FLOOR, ITEM_ID)
        count += 1

Map.log(f"Added {{count}} border items")
""",
    "count_items": """
# Count specific items on a floor
ITEM_ID = {item_id}
FLOOR = {floor}

positions = Map.find_items(ITEM_ID, floor=FLOOR)
Map.log(f"Found {{len(positions)}} instances of item {{ITEM_ID}}")
""",
}


def get_script_template(name: str, **kwargs: Any) -> str:
    """Get a script template with variables filled in.

    Args:
        name: Template name.
        **kwargs: Template variables.

    Returns:
        Formatted script string.
    """
    template = SCRIPT_TEMPLATES.get(name, "")
    if template and kwargs:
        return template.format(**kwargs)
    return template
