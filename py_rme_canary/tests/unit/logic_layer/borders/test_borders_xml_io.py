"""Tests for logic_layer.borders.borders_xml_io."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from py_rme_canary.logic_layer.borders.borders_xml_io import (
    KEY_TO_LEGACY_EDGE,
    LEGACY_EDGE_TO_KEY,
    LegacyBorderDef,
    export_borders_xml,
    import_borders_into_manager,
    parse_borders_xml,
)

# --- Edge mapping tests ---


class TestEdgeMappings:
    def test_all_cardinals(self) -> None:
        for edge in ("n", "e", "s", "w"):
            assert edge in LEGACY_EDGE_TO_KEY

    def test_convex_corners(self) -> None:
        for edge in ("cnw", "cne", "cse", "csw"):
            assert edge in LEGACY_EDGE_TO_KEY

    def test_diagonal_corners(self) -> None:
        for edge in ("dnw", "dne", "dse", "dsw"):
            assert edge in LEGACY_EDGE_TO_KEY

    def test_round_trip_mapping(self) -> None:
        for legacy, key in LEGACY_EDGE_TO_KEY.items():
            assert KEY_TO_LEGACY_EDGE[key] == legacy

    def test_twelve_total_edges(self) -> None:
        assert len(LEGACY_EDGE_TO_KEY) == 12
        assert len(KEY_TO_LEGACY_EDGE) == 12


# --- LegacyBorderDef ---


class TestLegacyBorderDef:
    def test_immutable(self) -> None:
        bdef = LegacyBorderDef(border_id=1, group=None, items={"NORTH": 100})
        with pytest.raises(AttributeError):
            bdef.border_id = 2  # type: ignore[misc]


# --- parse_borders_xml ---


SAMPLE_BORDERS_XML = """\
<?xml version="1.0"?>
<materials>
  <border id="58">
    <borderitem edge="n" item="1100"/>
    <borderitem edge="e" item="1101"/>
    <borderitem edge="s" item="1102"/>
    <borderitem edge="w" item="1103"/>
    <borderitem edge="cnw" item="1104"/>
    <borderitem edge="cne" item="1105"/>
    <borderitem edge="cse" item="1106"/>
    <borderitem edge="csw" item="1107"/>
    <borderitem edge="dnw" item="1108"/>
    <borderitem edge="dne" item="1109"/>
    <borderitem edge="dse" item="1110"/>
    <borderitem edge="dsw" item="1111"/>
  </border>
  <border id="59" group="3">
    <borderitem edge="n" item="2000"/>
  </border>
</materials>
"""


class TestParseBordersXml:
    def test_parse_sample(self, tmp_path: Path) -> None:
        xml_file = tmp_path / "borders.xml"
        xml_file.write_text(SAMPLE_BORDERS_XML, encoding="utf-8")

        result = parse_borders_xml(xml_file)
        assert len(result) == 2

        # First border
        b58 = result[0]
        assert b58.border_id == 58
        assert b58.group is None
        assert b58.items["NORTH"] == 1100
        assert b58.items["EAST"] == 1101
        assert b58.items["INNER_SW"] == 1111
        assert len(b58.items) == 12

        # Second border
        b59 = result[1]
        assert b59.border_id == 59
        assert b59.group == 3
        assert b59.items["NORTH"] == 2000

    def test_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            parse_borders_xml("/nonexistent/borders.xml")

    def test_empty_borders(self, tmp_path: Path) -> None:
        xml_file = tmp_path / "borders.xml"
        xml_file.write_text("<materials></materials>", encoding="utf-8")
        result = parse_borders_xml(xml_file)
        assert result == []

    def test_border_without_id(self, tmp_path: Path) -> None:
        xml_file = tmp_path / "borders.xml"
        xml_file.write_text(
            '<materials><border><borderitem edge="n" item="100"/></border></materials>',
            encoding="utf-8",
        )
        result = parse_borders_xml(xml_file)
        assert result == []

    def test_unknown_edge_ignored(self, tmp_path: Path) -> None:
        xml_file = tmp_path / "borders.xml"
        xml_file.write_text(
            '<materials><border id="1"><borderitem edge="unknown" item="100"/>'
            '<borderitem edge="n" item="200"/></border></materials>',
            encoding="utf-8",
        )
        result = parse_borders_xml(xml_file)
        assert len(result) == 1
        assert "NORTH" in result[0].items
        assert len(result[0].items) == 1

    def test_include_files(self, tmp_path: Path) -> None:
        # Main file includes a sub-file
        sub = tmp_path / "sub_borders.xml"
        sub.write_text(
            '<materials><border id="99"><borderitem edge="s" item="500"/></border></materials>',
            encoding="utf-8",
        )

        main = tmp_path / "borders.xml"
        main.write_text(
            '<materials><include file="sub_borders.xml"/></materials>',
            encoding="utf-8",
        )

        result = parse_borders_xml(main)
        assert len(result) == 1
        assert result[0].border_id == 99
        assert result[0].items["SOUTH"] == 500


# --- import_borders_into_manager ---


class TestImportBordersIntoManager:
    def test_basic_import(self) -> None:
        manager = MagicMock()
        manager.set_border_override = MagicMock(return_value=True)

        borders = [
            LegacyBorderDef(border_id=58, group=None, items={"NORTH": 100, "SOUTH": 200}),
        ]

        changed = import_borders_into_manager(manager, borders)
        assert changed == 2
        assert manager.set_border_override.call_count == 2

    def test_id_remapping(self) -> None:
        manager = MagicMock()
        manager.set_border_override = MagicMock(return_value=True)

        borders = [
            LegacyBorderDef(border_id=58, group=None, items={"NORTH": 100}),
        ]

        changed = import_borders_into_manager(
            manager, borders, border_id_to_server_id={58: 999}
        )
        assert changed == 1
        manager.set_border_override.assert_called_with(999, "NORTH", 100)

    def test_no_setter_method(self) -> None:
        manager = object()  # No set_border_override
        borders = [LegacyBorderDef(border_id=1, group=None, items={"NORTH": 100})]
        changed = import_borders_into_manager(manager, borders)
        assert changed == 0

    def test_empty_borders(self) -> None:
        manager = MagicMock()
        assert import_borders_into_manager(manager, []) == 0


# --- export_borders_xml ---


class TestExportBordersXml:
    def _make_brush(self, sid: int, borders: dict[str, int]) -> Any:
        brush = MagicMock()
        brush.server_id = sid
        brush.borders = borders
        brush.border_group = None
        return brush

    def _make_manager(self, brushes: dict[int, Any]) -> MagicMock:
        manager = MagicMock()
        manager._brushes = brushes
        return manager

    def test_basic_export(self, tmp_path: Path) -> None:
        b1 = self._make_brush(58, {"NORTH": 100, "SOUTH": 200})
        manager = self._make_manager({58: b1})

        out_path = tmp_path / "out.xml"
        count = export_borders_xml(manager, out_path)
        assert count == 1
        assert out_path.exists()

        # Parse back and verify
        parsed = parse_borders_xml(out_path)
        assert len(parsed) == 1
        assert parsed[0].border_id == 58
        assert parsed[0].items["NORTH"] == 100
        assert parsed[0].items["SOUTH"] == 200

    def test_empty_export(self, tmp_path: Path) -> None:
        manager = self._make_manager({})

        out_path = tmp_path / "out.xml"
        count = export_borders_xml(manager, out_path)
        assert count == 0
        assert out_path.exists()

    def test_roundtrip(self, tmp_path: Path) -> None:
        """Write -> Read -> Compare."""
        b1 = self._make_brush(10, {"NORTH": 111, "EAST": 222, "CORNER_NW": 333})
        manager = self._make_manager({10: b1})

        out_path = tmp_path / "roundtrip.xml"
        export_borders_xml(manager, out_path)

        parsed = parse_borders_xml(out_path)
        assert len(parsed) == 1
        assert parsed[0].border_id == 10
        assert parsed[0].items == {"NORTH": 111, "EAST": 222, "CORNER_NW": 333}
