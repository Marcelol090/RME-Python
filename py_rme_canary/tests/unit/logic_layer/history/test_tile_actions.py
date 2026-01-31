"""Unit tests for history primitives.

Validates HistoryManager behavior without relying on legacy tile action APIs.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from py_rme_canary.logic_layer.history import HistoryManager


@dataclass
class DummyAction:
    """Minimal action used to validate history stacks."""

    label: str
    has_changes_flag: bool = True
    undo_calls: int = 0
    redo_calls: int = 0

    def has_changes(self) -> bool:
        return bool(self.has_changes_flag)

    def undo(self, game_map) -> None:
        self.undo_calls += 1

    def redo(self, game_map) -> None:
        self.redo_calls += 1

    def describe(self) -> str:
        return self.label


@pytest.fixture
def history_manager() -> HistoryManager:
    """Create a fresh HistoryManager for each test."""
    return HistoryManager()


def test_commit_skips_action_without_changes(history_manager: HistoryManager) -> None:
    """HistoryManager should ignore actions with no changes."""
    action = DummyAction("NoOp", has_changes_flag=False)
    history_manager.commit_action(action)
    assert history_manager.undo_stack == []


def test_commit_and_undo_redo_cycle(history_manager: HistoryManager) -> None:
    """HistoryManager should push to undo and cycle through redo properly."""
    action = DummyAction("Paint")
    history_manager.commit_action(action)

    assert len(history_manager.undo_stack) == 1
    assert history_manager.redo_stack == []

    restored = history_manager.undo(game_map=object())
    assert restored is action
    assert action.undo_calls == 1
    assert history_manager.undo_stack == []
    assert history_manager.redo_stack == [action]

    redone = history_manager.redo(game_map=object())
    assert redone is action
    assert action.redo_calls == 1
    assert history_manager.undo_stack == [action]
    assert history_manager.redo_stack == []


def test_undo_redo_empty_returns_none(history_manager: HistoryManager) -> None:
    """HistoryManager should return None when stacks are empty."""
    assert history_manager.undo(game_map=object()) is None
    assert history_manager.redo(game_map=object()) is None
