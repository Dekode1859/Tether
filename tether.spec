import sys
from pathlib import Path

block_cipher = None

project_root = Path(SPECPATH)
app_dir = project_root / "app"
core_dir = project_root / "core"
jobs_dir = project_root / "jobs"
models_dir = project_root / "models"

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(core_dir / "prompts.py"), "core"),
        (str(models_dir), "models"),
    ],
    hiddenimports=[
        "pystray",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageFilter",
        "keyboard",
        "sounddevice",
        "sounddevice",
        "faster_whisper",
        "faster_whisper WhisperModel",
        "faster_whisper.transcribe",
        "ctypes",
        "ctypes.wintypes",
        "schedule",
        "plyer",
        "plyer.facades",
        "plyer.facades.Notification",
        "httpx",
        "httpx._transports",
        "httpx._transports.default",
        "ollama",
        "numpy",
        "onnxruntime",
        "onnxruntime.capi",
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
    name="Tether",
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
    icon=None,
)
