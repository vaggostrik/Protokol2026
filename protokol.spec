# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None

extra_datas = []
if Path('resources').exists():
    extra_datas.append(('resources', 'resources'))

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=extra_datas,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtPrintSupport',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.pool',
        'reportlab.graphics',
        'reportlab.platypus',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.pdfbase.ttfonts',
        'email.mime.multipart',
        'email.mime.text',
        'email.mime.base',
        'PIL._tkinter_finder',
        'PIL.Image',
        'win32com.client',   # WIA scanner
        'win32com.shell',
        'pywintypes',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas', 'twain'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Protokol2026',
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
    # icon='resources/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Protokol2026',
)
