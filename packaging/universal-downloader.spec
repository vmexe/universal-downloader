# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Universal Downloader GUI.

Build on each OS to produce a native binary:
    pyinstaller --clean --noconfirm packaging/universal-downloader.spec

Produces a one-folder build (recommended for the heavy yt-dlp/spotdl/gallery-dl
dependencies):
    Linux   : dist/universal-downloader/universal-downloader
    Windows : dist/universal-downloader/universal-downloader.exe
    macOS   : dist/universal-downloader/universal-downloader
"""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

# Project root lives one directory above this spec file. PyInstaller runs the
# spec with ``SPECPATH`` (the containing directory) defined as a global.
PROJECT_ROOT = Path(SPECPATH).parent

datas = []
binaries = []

# Engines are imported lazily from the factory, so collect their submodules
# explicitly to guarantee they are bundled.
hiddenimports = list(
    collect_submodules("downloader.core.engines")
) + collect_submodules("spotdl") + collect_submodules("gallery_dl")

# Bundle a local ffmpeg binary (if a path is provided via FFMPEG_PATH env var)
# so audio/video post-processing works in the packaged app without requiring a
# system install. The build workflow sets this on every platform.
ffmpeg_path = os.environ.get("FFMPEG_PATH")
if ffmpeg_path and Path(ffmpeg_path).exists():
    binaries.append((ffmpeg_path, "."))

block_cipher = None

a = Analysis(
    [str(PROJECT_ROOT / "downloader" / "app" / "main.py")],
    pathex=[str(PROJECT_ROOT)],
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
