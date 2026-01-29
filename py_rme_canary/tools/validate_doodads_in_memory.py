from __future__ import annotations

"""In-memory validations for DoodadBrush semantics.

Run:
    python -m py_rme_canary.tools.validate_doodads_in_memory

Goal: quick sanity checks for the Qt-free doodad pipeline:
- alternates via brush_variation
- deterministic weighted pick
- composite multi-tile placement (stack semantics)
- on_duplicate / draggable / on_blocking minimal semantics
- redo_borders pass does not crash
"""

from dataclasses import replace

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.logic_layer.brush_definitions import VIRTUAL_DOODAD_BASE, BrushManager
from py_rme_canary.logic_layer.transactional_brush import HistoryManager, TransactionalBrushStroke


def _top_item_id(m: GameMap, x: int, y: int, z: int) -> int | None:
    t = m.get_tile(int(x), int(y), int(z))
    if t is None:
        return None
    if t.items:
        return int(t.items[-1].id)
    return None


def _item_ids(m: GameMap, x: int, y: int, z: int) -> list[int]:
    t = m.get_tile(int(x), int(y), int(z))
    if t is None or not t.items:
        return []
    return [int(it.id) for it in t.items]


def main() -> None:
    bm = BrushManager.from_json_file("data/brushes.json")
    ok = bm.ensure_doodads_loaded("data/materials/brushs.xml")
    assert ok, "expected doodad materials to load"

    # === 1) Deterministic weighted pick (single items)
    # green trees: lookid=3621; multiple <item chance=...>
    sid_green_trees = int(VIRTUAL_DOODAD_BASE + 3621)

    m1 = GameMap(header=MapHeader(otbm_version=1, width=50, height=50))
    h1 = HistoryManager()
    s1 = TransactionalBrushStroke(game_map=m1, brush_manager=bm, history=h1, auto_border_enabled=False)
    s1.brush_variation = 0
    s1.begin(x=10, y=10, z=7, selected_server_id=sid_green_trees)
    s1.end()
    chosen1 = _top_item_id(m1, 10, 10, 7)
    assert chosen1 is not None and chosen1 > 0

    m2 = GameMap(header=MapHeader(otbm_version=1, width=50, height=50))
    h2 = HistoryManager()
    s2 = TransactionalBrushStroke(game_map=m2, brush_manager=bm, history=h2, auto_border_enabled=False)
    s2.brush_variation = 0
    s2.begin(x=10, y=10, z=7, selected_server_id=sid_green_trees)
    s2.end()
    chosen2 = _top_item_id(m2, 10, 10, 7)
    assert chosen2 == chosen1, f"expected deterministic pick, got {chosen1} vs {chosen2}"

    # === 2) Composite multi-tile placement + alternates (brick wall arch)
    # Two alternates, both composite-only.
    sid_arch = int(VIRTUAL_DOODAD_BASE + 1627)

    m3 = GameMap(header=MapHeader(otbm_version=1, width=50, height=50))
    h3 = HistoryManager()
    s3 = TransactionalBrushStroke(game_map=m3, brush_manager=bm, history=h3, auto_border_enabled=True)
    s3.brush_variation = 0  # pick first <alternate>
    s3.begin(x=10, y=10, z=7, selected_server_id=sid_arch)
    act3 = s3.end()
    assert act3 is not None

    # First alternate is horizontal: (0,0)=1626, (1,0)=1627
    assert _top_item_id(m3, 10, 10, 7) == 1626
    assert _top_item_id(m3, 11, 10, 7) == 1627

    # Alternate selection via brush_variation should be stable and distinct.
    m3b = GameMap(header=MapHeader(otbm_version=1, width=50, height=50))
    h3b = HistoryManager()
    s3b = TransactionalBrushStroke(game_map=m3b, brush_manager=bm, history=h3b, auto_border_enabled=False)
    s3b.brush_variation = 1  # pick second <alternate>
    s3b.begin(x=10, y=10, z=7, selected_server_id=sid_arch)
    s3b.end()

    # Second alternate is vertical: (0,0)=1624, (0,1)=1625
    assert _top_item_id(m3b, 10, 10, 7) == 1624
    assert _top_item_id(m3b, 10, 11, 7) == 1625

    # === 3) on_duplicate=false (default) should block placing owned items twice.
    mdup = GameMap(header=MapHeader(otbm_version=1, width=50, height=50))
    hdup = HistoryManager()
    sdup = TransactionalBrushStroke(game_map=mdup, brush_manager=bm, history=hdup, auto_border_enabled=False)
    sdup.brush_variation = 0
    sdup.begin(x=10, y=10, z=7, selected_server_id=sid_arch)
    sdup.end()
    assert _item_ids(mdup, 10, 10, 7) == [1626]
    assert _item_ids(mdup, 11, 10, 7) == [1627]

    # Apply again at the same position: should not duplicate items.
    sdup2 = TransactionalBrushStroke(game_map=mdup, brush_manager=bm, history=hdup, auto_border_enabled=False)
    sdup2.brush_variation = 0
    sdup2.begin(x=10, y=10, z=7, selected_server_id=sid_arch)
    sdup2.end()
    assert _item_ids(mdup, 10, 10, 7) == [1626]
    assert _item_ids(mdup, 11, 10, 7) == [1627]

    # === 4) one_size=true should ignore footprint/smear (ramp)
    sid_ramp = int(VIRTUAL_DOODAD_BASE + 1957)

    msize = GameMap(header=MapHeader(otbm_version=1, width=50, height=50))
    hsize = HistoryManager()
    ssize = TransactionalBrushStroke(game_map=msize, brush_manager=bm, history=hsize, auto_border_enabled=False)
    ssize.brush_variation = 0
    ssize.begin(x=10, y=10, z=7, selected_server_id=sid_ramp)
    ssize.paint(x=11, y=10, z=7, selected_server_id=sid_ramp)
    ssize.end()
    assert _top_item_id(msize, 10, 10, 7) is not None
    assert _top_item_id(msize, 11, 10, 7) is None, "expected one_size=true to ignore non-origin tiles"

    # === 5) draggable=false should not smear (moon sculpture)
    sid_moon = int(VIRTUAL_DOODAD_BASE + 25495)

    m4 = GameMap(header=MapHeader(otbm_version=1, width=50, height=50))
    # Minimal on_blocking=false approximation requires ground.
    m4.set_tile(replace(m4.ensure_tile(10, 10, 7), ground=Item(id=4526)))
    m4.set_tile(replace(m4.ensure_tile(11, 10, 7), ground=Item(id=4526)))

    h4 = HistoryManager()
    s4 = TransactionalBrushStroke(game_map=m4, brush_manager=bm, history=h4, auto_border_enabled=False)
    s4.brush_variation = 0
    s4.begin(x=10, y=10, z=7, selected_server_id=sid_moon)
    # Simulate drag across one tile; should be ignored.
    s4.paint(x=11, y=10, z=7, selected_server_id=sid_moon)
    s4.end()

    assert _top_item_id(m4, 10, 10, 7) is not None
    assert _top_item_id(m4, 11, 10, 7) is None, "expected draggable=false to not smear"

    print("OK: doodad in-memory validations passed")


if __name__ == "__main__":
    main()
