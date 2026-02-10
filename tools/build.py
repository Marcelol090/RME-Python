#!/usr/bin/env python3
"""Build script for Canary Map Editor.

Creates a standalone executable using PyInstaller with version info,
data bundles, and proper hidden imports for PyQt6 + OpenGL.
"""
from __future__ import annotations

import datetime
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Resolve paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
ENTRY_POINT = PROJECT_ROOT / "py_rme_canary" / "vis_layer" / "qt_app.py"

sys.path.insert(0, str(PROJECT_ROOT))


def _get_version_info() -> tuple[str, tuple[int, int, int, int]]:
    """Import version from the project."""
    from py_rme_canary.core.version import get_build_info
    info = get_build_info()
    file_ver = (info.major, info.minor, info.patch, info.build_number)
    return info.semver, file_ver


def _write_version_file(version_str: str, file_ver: tuple[int, int, int, int]) -> Path:
    """Generate a PyInstaller-compatible Windows version info file."""
    content = f"""# UTF-8
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers={file_ver},
        prodvers={file_ver},
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo([
            StringTable(
                '040904B0',
                [
                    StringStruct('CompanyName', 'PyRME Canary Project'),
                    StringStruct('FileDescription', 'Canary Map Editor'),
                    StringStruct('FileVersion', '{version_str}'),
                    StringStruct('InternalName', 'CanaryMapEditor'),
                    StringStruct('OriginalFilename', 'CanaryMapEditor.exe'),
                    StringStruct('ProductName', 'Canary Map Editor'),
                    StringStruct('ProductVersion', '{version_str}'),
                    StringStruct('LegalCopyright', 'MIT License'),
                ],
            )
        ]),
        VarFileInfo([VarStruct('Translation', [0x0409, 1200])]),
    ],
)
"""
    tmp = Path(tempfile.mktemp(suffix="_version.py"))
    tmp.write_text(content, encoding="utf-8")
    return tmp


def clean_build_dirs() -> None:
    """Remove previous build artifacts."""
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            print(f"Cleaning {d}...")
            shutil.rmtree(d)


def run_pyinstaller() -> None:
    """Run PyInstaller with optimal settings including version info."""
    print("Starting build process...")

    version_str, file_ver = _get_version_info()
    print(f"Building version: {version_str}")

    version_file = _write_version_file(version_str, file_ver)

    # Inject build metadata via env vars
    env = os.environ.copy()
    env["PYRME_CHANNEL"] = env.get("PYRME_CHANNEL", "stable")
    env["PYRME_BUILD_DATE"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            env["PYRME_COMMIT"] = result.stdout.strip()
    except Exception:
        pass

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--name=CanaryMapEditor",
        "--windowed",
        "--onefile",
        f"--paths={PROJECT_ROOT}",
        "--exclude-module=PySide6",
        "--exclude-module=PyQt5",
        "--exclude-module=PySide2",
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=PyQt6.QtOpenGL",
        "--hidden-import=PyQt6.QtOpenGLWidgets",
        "--hidden-import=OpenGL",
        "--hidden-import=OpenGL.GL",
        "--hidden-import=OpenGL.arrays.arraydatatype",
        "--hidden-import=OpenGL.raw.GL.VERSION.GL_1_1",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=defusedxml",
        "--hidden-import=defusedxml.ElementTree",
        "--hidden-import=pkgutil",
        "--hidden-import=importlib",
        "--hidden-import=importlib.metadata",
        "--hidden-import=importlib.resources",
        "--hidden-import=typing_extensions",
        "--collect-submodules=PyQt6",
        f"--add-data={(PROJECT_ROOT / 'data')}{os.pathsep}data",
        f"--add-data={(PROJECT_ROOT / 'py_rme_canary' / 'data')}{os.pathsep}py_rme_canary/data",
        f"--version-file={version_file}",
        str(ENTRY_POINT),
    ]

    try:
        subprocess.run(cmd, check=True, env=env)
        exe_path = DIST_DIR / "CanaryMapEditor.exe"
        print(f"\nBuild success! ({version_str})")
        print(f"Executable: {exe_path}")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Size: {size_mb:.1f} MB")
    except subprocess.CalledProcessError as e:
        print(f"Build failed (exit {e.returncode})")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: PyInstaller not found. pip install pyinstaller")
        sys.exit(1)
    finally:
        version_file.unlink(missing_ok=True)


if __name__ == "__main__":
    clean_build_dirs()
    run_pyinstaller()
