# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all keyboard submodules
keyboard_submodules = collect_submodules('keyboard')
pynput_submodules = collect_submodules('pynput')
# Collect data files for keyboard (if any)
keyboard_datas = collect_data_files('keyboard', includes=['*.dll', '*.pyd'])

a = Analysis(
    ['main.py'],
    pathex=['src'],
    binaries=[],
    datas=keyboard_datas,
    hiddenimports=[
        'keyboard',
        'keyboard._generic',
        'keyboard._keyboard_event',
        'keyboard._nixkeyboard',
        'keyboard._winkeyboard',
        'keyboard._canonical_names',
        'keyboard._mouse_event',
        'keyboard._queue',
        'pynput',
        'pynput.mouse',
        'pynput.keyboard',
        'pynput.mouse._win32',
        'pynput.keyboard._win32',
        'cv2',
        'numpy',
        'PIL',
        'PIL.Image',
        'pytesseract',
        'win32gui',
        'win32api',
        'win32con',
        'win32ui',
        'win32process',
        'ctypes',
        'ctypes.wintypes',
    ] + keyboard_submodules + pynput_submodules,
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
    name='main',
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
