from __future__ import annotations

from pathlib import Path

import pytest

from py_rme_canary.core.io.map_detection import MAGIC_OTBM, MAGIC_OTMM, detect_map_file
from py_rme_canary.core.io.otmm import OTMMError, load_otmm


def _write_magic(path: Path, magic: bytes) -> Path:
    path.write_bytes(magic + b"\x00\x00")
    return path


def test_detect_otmm_magic(tmp_path: Path) -> None:
    p = _write_magic(tmp_path / "tests_tmp.otmm", MAGIC_OTMM)
    res = detect_map_file(p)
    assert res.kind == "otmm"


def test_detect_otbm_magic_with_otmm_extension(tmp_path: Path) -> None:
    p = _write_magic(tmp_path / "tests_tmp.otmm", MAGIC_OTBM)
    res = detect_map_file(p)
    assert res.kind == "otbm"


def test_load_otmm_not_implemented(tmp_path: Path) -> None:
    p = _write_magic(tmp_path / "sample.otmm", MAGIC_OTMM)
    with pytest.raises(OTMMError):
        load_otmm(p)
