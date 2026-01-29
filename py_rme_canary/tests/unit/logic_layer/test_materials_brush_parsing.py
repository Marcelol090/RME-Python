from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from py_rme_canary.logic_layer.brush_definitions import BrushManager


def _write_materials(tmp_path: Path, include_name: str, include_body: str) -> Path:
    root_xml = dedent(f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <materials>
            <include file="{include_name}"/>
        </materials>
    """).strip()
    root_path = tmp_path / "materials.xml"
    root_path.write_text(root_xml, encoding="utf-8")
    (tmp_path / include_name).write_text(dedent(include_body).strip(), encoding="utf-8")
    return root_path


def test_table_materials_default_chance_and_lookid(tmp_path: Path) -> None:
    include_xml = """
        <?xml version="1.0" encoding="UTF-8"?>
        <materials>
            <brush name="Table One" type="table" lookid="1000">
                <table align="north">
                    <item id="2001"/>
                </table>
            </brush>
        </materials>
    """
    root_path = _write_materials(tmp_path, "tables.xml", include_xml)

    mgr = BrushManager()
    mgr.load_table_brushes_from_materials(str(root_path))

    spec = mgr._table_brushes.get(1000)
    assert spec is not None
    choice = spec.items_by_alignment["north"][0]
    assert choice.id == 2001
    assert choice.chance == 1
    assert spec.server_id == 1000
    assert not mgr._table_brushes_warnings


def test_table_materials_negative_chance_warns(tmp_path: Path) -> None:
    include_xml = """
        <?xml version="1.0" encoding="UTF-8"?>
        <materials>
            <brush name="Table Bad" type="table" server_lookid="1100">
                <table align="south">
                    <item id="3001" chance="-5"/>
                </table>
            </brush>
        </materials>
    """
    root_path = _write_materials(tmp_path, "tables.xml", include_xml)

    mgr = BrushManager()
    mgr.load_table_brushes_from_materials(str(root_path))

    spec = mgr._table_brushes.get(1100)
    assert spec is not None
    choice = spec.items_by_alignment["south"][0]
    assert choice.id == 3001
    assert choice.chance == 0
    assert any("negative" in msg for msg in mgr._table_brushes_warnings)


def test_carpet_materials_missing_chance_skips_local_id(tmp_path: Path) -> None:
    include_xml = """
        <?xml version="1.0" encoding="UTF-8"?>
        <materials>
            <brush name="Carpet Mixed" type="carpet" server_lookid="2100">
                <carpet align="center" id="5000">
                    <item id="5001"/>
                </carpet>
                <carpet align="north">
                    <item id="5002" chance="7"/>
                </carpet>
            </brush>
        </materials>
    """
    root_path = _write_materials(tmp_path, "carpets.xml", include_xml)

    mgr = BrushManager()
    mgr.load_carpet_brushes_from_materials(str(root_path))

    spec = mgr._carpet_brushes.get(2100)
    assert spec is not None
    assert "north" in spec.items_by_alignment
    assert "center" not in spec.items_by_alignment
    choice = spec.items_by_alignment["north"][0]
    assert choice.id == 5002
    assert choice.chance == 7
    assert any("missing chance" in msg for msg in mgr._carpet_brushes_warnings)


def test_carpet_materials_local_id_fallback(tmp_path: Path) -> None:
    include_xml = """
        <?xml version="1.0" encoding="UTF-8"?>
        <materials>
            <brush name="Carpet Local" type="carpet" server_lookid="2200">
                <carpet align="center" id="6000"/>
            </brush>
        </materials>
    """
    root_path = _write_materials(tmp_path, "carpets.xml", include_xml)

    mgr = BrushManager()
    mgr.load_carpet_brushes_from_materials(str(root_path))

    spec = mgr._carpet_brushes.get(2200)
    assert spec is not None
    choice = spec.items_by_alignment["center"][0]
    assert choice.id == 6000
    assert choice.chance == 1
    assert not mgr._carpet_brushes_warnings
