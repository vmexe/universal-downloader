# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Universal Downloader GUI.

Build on each OS to produce a native binary:
    pyinstaller packaging/universal-downloader.spec

Produces:
    Linux   : dist/universal-downloader       (executable)
    macOS   : dist/UniversalDownloader.app    (app bundle)
    Windows : dist/UniversalDownloader.exe    (console-less windowed exe)
"""

from pathlib import Path

import PyInstaller.utils.hooks as hooks

# Bundle the app metadata / config so engines find sane defaults.
datas = []
binaries = []
hiddenimports = [
    "yt_dlp",
    "spotdl",
    "gallery_dl",
    "downloader.core.engines.factory",
]

# Include ffmpeg if detected on the PATH (yt-dlp post-processing needs it).
import shutil  # noqa: E402

ffmpeg = shutil.which("ffmpeg")
if ffmpeg:
    binaries += hooks.collect_dynamic_libs("")

block_cipher = None

a = Analysis(
    ["../downloader/app/main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="universal-downloader",
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="universal-downloader",
)
