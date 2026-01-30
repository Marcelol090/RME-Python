#!/usr/bin/env python3
"""
Build script for py_rme_canary.
Creates a standalone executable using PyInstaller.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Project root setup
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
ENTRY_POINT = PROJECT_ROOT / "py_rme_canary" / "vis_layer" / "qt_app.py"
ICON_PATH = PROJECT_ROOT / "py_rme_canary" / "icons" / "editor_icon.ico"  # Assuming icon exists


def clean_build_dirs():
    """Remove previous build artifacts."""
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            print(f"Cleaning {d}...")
            shutil.rmtree(d)


def run_pyinstaller():
    """Run PyInstaller with optimal settings."""
    print("Starting build process...")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name=CanaryMapEditor",
        "--windowed",  # No console window
        "--onefile",  # Single executable (easier distribution)
        # Paths
        f"--paths={PROJECT_ROOT}",
        # Exclude conflicting Qt bindings
        "--exclude-module=PySide6",
        "--exclude-module=PyQt5",
        "--exclude-module=PySide2",
        # Hidden imports (often missed by auto-analysis)
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
        # Data files
        f"--add-data={(PROJECT_ROOT / 'data')}{os.pathsep}data",
        f"--add-data={(PROJECT_ROOT / 'py_rme_canary' / 'data')}{os.pathsep}py_rme_canary/data",
        "--hidden-import=defusedxml",
        "--hidden-import=defusedxml.ElementTree",
        # Standard library modules often missed
        "--hidden-import=pkgutil",
        "--hidden-import=importlib",
        "--hidden-import=importlib.metadata",
        "--hidden-import=importlib.resources",
        "--hidden-import=typing_extensions",
        "--collect-submodules=PyQt6",
        # Data files (add as needed)
        # "--add-data=py_rme_canary/data;data",
        # Icon
        # f"--icon={ICON_PATH}",
        # Entry point
        str(ENTRY_POINT),
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"Build success! Executable at: {DIST_DIR / 'CanaryMapEditor.exe'}")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error code {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: PyInstaller not found. Please run: pip install pyinstaller")
        sys.exit(1)


if __name__ == "__main__":
    if not os.path.exists("py_rme_canary"):
        print("Error: Run this script from the project root or ensure package structure.")
        # sys.exit(1) # Warning only for now as we resolve paths

    clean_build_dirs()
    run_pyinstaller()
