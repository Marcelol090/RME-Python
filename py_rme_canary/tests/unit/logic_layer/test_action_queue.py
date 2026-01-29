from __future__ import annotations

from py_rme_canary.logic_layer.session.action_queue import (
    ActionType,
    CompositeAction,
    SessionAction,
    SessionActionQueue,
)


class DummyAction:
    def __init__(self, name: str) -> None:
        self._name = str(name)

    def has_changes(self) -> bool:
        return True

    def undo(self, _game_map: object) -> None:
        return None

    def redo(self, _game_map: object) -> None:
        return None

    def describe(self) -> str:
        return self._name


def test_queue_merges_with_default_delay() -> None:
    times = iter([100.0, 101.0])

    def clock() -> float:
        return float(next(times))

    queue = SessionActionQueue(clock=clock)
    queue.push(SessionAction(type=ActionType.PAINT, action=DummyAction("a1")))
    queue.push(SessionAction(type=ActionType.PAINT, action=DummyAction("a2")))

    assert len(queue.items) == 1
    merged = queue.items[0]
    assert merged.label == "Paint"
    assert isinstance(merged.action, CompositeAction)
    assert len(merged.action.actions) == 2


def test_queue_does_not_merge_without_delay() -> None:
    times = iter([200.0, 201.0])

    def clock() -> float:
        return float(next(times))

    queue = SessionActionQueue(clock=clock)
    queue.push(SessionAction(type=ActionType.SET_WAYPOINT, action=DummyAction("one")))
    queue.push(SessionAction(type=ActionType.SET_WAYPOINT, action=DummyAction("two")))

    assert len(queue.items) == 2


def test_reset_timer_prevents_merge() -> None:
    times = iter([300.0, 301.0])

    def clock() -> float:
        return float(next(times))

    queue = SessionActionQueue(clock=clock)
    queue.push(SessionAction(type=ActionType.PAINT, action=DummyAction("first")))
    queue.reset_timer()
    queue.push(SessionAction(type=ActionType.PAINT, action=DummyAction("second")))

    assert len(queue.items) == 2
