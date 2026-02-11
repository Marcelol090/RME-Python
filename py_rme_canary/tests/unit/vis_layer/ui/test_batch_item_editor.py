"""Tests for batch item editor dialog widgets."""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")


@pytest.fixture
def app():
    from PyQt6.QtWidgets import QApplication

    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


def test_item_selector_browse_callback_sets_item_id(app):
    from py_rme_canary.vis_layer.ui.dialogs.batch_item_editor import ItemIdSelector

    selector = ItemIdSelector()
    selector.set_browse_callback(lambda current: 4321)

    selector._on_browse_clicked()

    assert selector.item_id == 4321


def test_item_selector_browse_cancel_keeps_item_id(app):
    from py_rme_canary.vis_layer.ui.dialogs.batch_item_editor import ItemIdSelector

    selector = ItemIdSelector()
    selector.item_id = 111
    selector.set_browse_callback(lambda current: None)

    selector._on_browse_clicked()

    assert selector.item_id == 111


def test_item_selector_uses_dialog_fallback_when_callback_missing(app, monkeypatch):
    from py_rme_canary.vis_layer.ui.dialogs.batch_item_editor import ItemIdSelector

    selector = ItemIdSelector()
    monkeypatch.setattr(selector, "_open_browser_with_dialog", lambda: 777)

    selector._on_browse_clicked()

    assert selector.item_id == 777


def test_batch_editor_sets_browser_for_both_selectors(app):
    from py_rme_canary.vis_layer.ui.dialogs.batch_item_editor import BatchItemEditor

    dialog = BatchItemEditor()
    dialog.set_item_browser(lambda current: 999 if current <= 0 else current + 1)

    dialog.source_selector.item_id = 0
    dialog.target_selector.item_id = 7

    dialog.source_selector._on_browse_clicked()
    dialog.target_selector._on_browse_clicked()

    assert dialog.source_selector.item_id == 999
    assert dialog.target_selector.item_id == 8
