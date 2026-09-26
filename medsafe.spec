# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification file for MEDSAFE.

Builds a standalone Windows ONEDIR desktop application.
Collects CustomTkinter themes and assets, win11toast, and WinRT notification modules.
Excludes testing frameworks and developer-only artifacts.
"""

from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

# 1. Collect CustomTkinter package assets, fonts, and themes
ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all('customtkinter')

# 2. Collect WinRT submodules required by win11toast for native Windows notifications
winrt_imports = collect_submodules('winrt')

datas = [
    ('assets', 'assets'),
] + ctk_datas

binaries = ctk_binaries

hiddenimports = list(set(
    [
        'customtkinter',
        'win11toast',
        'winrt',
        'sqlite3',
    ]
    + ctk_hiddenimports
    + winrt_imports
))

a = Analysis(
    ['frontend/main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        '_pytest',
        'tests',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MedSafe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/medsafe.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MedSafe',
)
