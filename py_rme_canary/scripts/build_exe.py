import os
import shutil
import sys
from pathlib import Path

import PyInstaller.__main__

# Define project root (assuming script is in py_rme_canary/scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ENTRY_POINT = PROJECT_ROOT / "vis_layer" / "qt_app.py"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"


def build():
    """Run PyInstaller to build the executable."""
    print("Starting build for PyRME Canary...")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Dir: {DATA_DIR}")
    print(f"Entry Point: {ENTRY_POINT}")

    # Clean previous builds
    if DIST_DIR.exists():
        print(f"Cleaning {DIST_DIR}...")
        shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists():
        print(f"Cleaning {BUILD_DIR}...")
        shutil.rmtree(BUILD_DIR)

    # Ensure data directory exists
    if not DATA_DIR.exists():
        print(f"ERROR: Data directory not found at {DATA_DIR}")
        sys.exit(1)

    # PyInstaller arguments
    # Note: On Windows, separator for --add-data is ';'
    sep = ";" if os.name == "nt" else ":"

    args = [
        str(ENTRY_POINT),
        "--name=PyRME_Canary",
        "--onedir",  # Generate a directory (easier for debugging)
        "--console",  # Keep console open for debug output (Canary build)
        "--clean",
        f"--add-data={DATA_DIR}{sep}data",  # Bundle data folder
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        # Add any other hidden imports here
    ]

    # Run PyInstaller
    try:
        PyInstaller.__main__.run(args)
        print("\nBuild successful!")
        print(f"Executable located at: {DIST_DIR / 'PyRME_Canary' / 'PyRME_Canary.exe'}")
    except Exception as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build()
