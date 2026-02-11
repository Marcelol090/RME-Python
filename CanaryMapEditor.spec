remeres-map-editor-redux# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtOpenGL', 'PyQt6.QtOpenGLWidgets', 'OpenGL', 'OpenGL.GL', 'OpenGL.arrays.arraydatatype', 'OpenGL.raw.GL.VERSION.GL_1_1', 'PIL', 'PIL.Image', 'defusedxml', 'defusedxml.ElementTree', 'pkgutil', 'importlib', 'importlib.metadata', 'importlib.resources', 'typing_extensions']
hiddenimports += collect_submodules('PyQt6')


a = Analysis(
    ['C:\\Users\\Marcelo Henrique\\Desktop\\projec_rme\\py_rme_canary\\vis_layer\\qt_app.py'],
    pathex=['C:\\Users\\Marcelo Henrique\\Desktop\\projec_rme'],
    binaries=[],
    datas=[('C:\\Users\\Marcelo Henrique\\Desktop\\projec_rme\\data', 'data'), ('C:\\Users\\Marcelo Henrique\\Desktop\\projec_rme\\py_rme_canary\\data', 'py_rme_canary/data')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6', 'PyQt5', 'PySide2'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CanaryMapEditor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='C:\\Users\\MARCEL~1\\AppData\\Local\\Temp\\tmpdg7di2ta_version.py',
)
