"""
Tests for AssetLoaderWizard.
"""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWizard

from py_rme_canary.vis_layer.ui.dialogs.asset_loader_wizard import AssetLoaderWizard
from py_rme_canary.vis_layer.ui.dialogs.client_data_loader_dialog import ClientDataLoadConfig


def test_wizard_creation(qtbot):
    """Test AssetLoaderWizard creation."""
    wizard = AssetLoaderWizard()
    qtbot.addWidget(wizard)
    wizard.show()

    assert wizard.windowTitle() == "Load Client Assets"
    assert len(wizard.pageIds()) == 4

def test_wizard_navigation(qtbot):
    """Test navigating through pages."""
    defaults = ClientDataLoadConfig("test/path", "auto", 1330, "", "", True)
    wizard = AssetLoaderWizard(defaults=defaults)
    qtbot.addWidget(wizard)
    wizard.show()
    qtbot.waitExposed(wizard)

    # Page 1: Intro
    assert wizard.currentId() == wizard.pageIds()[0]
    assert wizard.intro_page.title() == "Welcome"

    # Next (Intro -> Client)
    next_btn = wizard.button(QWizard.WizardButton.NextButton)
    assert next_btn.isEnabled()
    qtbot.mouseClick(next_btn, Qt.MouseButton.LeftButton)

    # Check page changed
    assert wizard.currentId() == wizard.pageIds()[1] # Client Page

    # Client Page Logic
    client_page = wizard.client_page
    assert client_page.path_edit.text() == "test/path"

    # Path invalid (test/path doesn't exist) -> Next disabled?
    # QWizard validates via isComplete()
    # Mock existence: We can't easily mock os.path.exists here without monkeypatch,
    # but we can set text to a valid directory (current dir).
    client_page.path_edit.setText(".")

    # Wait for isComplete to re-evaluate (usually immediate on textChanged)
    assert client_page.isComplete()
    assert next_btn.isEnabled()

    # Next (Client -> Metadata)
    qtbot.mouseClick(next_btn, Qt.MouseButton.LeftButton)
    assert wizard.currentId() == wizard.pageIds()[2] # Metadata Page

    # Next (Metadata -> Validation)
    qtbot.mouseClick(next_btn, Qt.MouseButton.LeftButton)
    assert wizard.currentId() == wizard.pageIds()[3] # Validation Page

    # Validation Page Logic
    # It auto-completes after 500ms
    qtbot.wait(1000) # Wait for timer

    # Finish button should be enabled if complete
    finish_btn = wizard.button(QWizard.WizardButton.FinishButton)
    # Validation logic checks client_page.get_assets_path() existence again.
    # Since we set it to ".", it should pass.
    assert finish_btn.isEnabled()

def test_wizard_config(qtbot):
    """Test get_config()."""
    defaults = ClientDataLoadConfig("/tmp", "modern", 1330, "/tmp/items.otb", "/tmp/items.xml", True)
    wizard = AssetLoaderWizard(defaults=defaults)
    qtbot.addWidget(wizard)
    wizard.show()

    # Directly verify pages propagate defaults (now in __init__)
    assert wizard.client_page.get_assets_path() == "/tmp"
    assert wizard.client_page.get_prefer_kind() == "modern"
    assert wizard.metadata_page.get_otb_path() == "/tmp/items.otb"

    # Verify final config object
    cfg = wizard.get_config()
    assert cfg.assets_path == "/tmp"
    assert cfg.client_version_hint == 1330
    assert cfg.items_otb_path == "/tmp/items.otb"
    assert cfg.items_xml_path == "/tmp/items.xml"
