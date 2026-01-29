# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Marcelo Henrique\\Desktop\\projec_rme\\py_rme_canary\\vis_layer\\qt_app.py'],
    pathex=['C:\\Users\\Marcelo Henrique\\Desktop\\projec_rme'],
    binaries=[],
    datas=[],
    hiddenimports=['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtOpenGL', 'PyQt6.QtOpenGLWidgets', 'OpenGL', 'OpenGL.GL', 'PIL', 'PIL.Image'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
)
