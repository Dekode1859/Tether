import sys
from pathlib import Path

block_cipher = None

project_root = Path(SPECPATH)
engine_dir = project_root / "engine"

a = Analysis(
    ["engine/main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(engine_dir / "ai" / "prompts.py"), "engine/ai"),
    ],
    hiddenimports=[
        "sounddevice",
        "faster_whisper",
        "faster_whisper.WhisperModel",
        "numpy",
        "httpx",
        "onnxruntime",
        "ctranslate2",
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="tether-engine",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
