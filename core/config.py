import os
from pathlib import Path

BASE_DIR = Path(os.path.expanduser("~/.tether"))
RAW_DIR = BASE_DIR / "raw"
AUDIO_DIR = BASE_DIR / "audio"
SUMMARIES_DIR = BASE_DIR / "summaries"

HOTKEY_DEFAULT = "ctrl+shift+space"
WHISPER_MODEL = "small.en"
OLLAMA_MODEL = "llama3"
OLLAMA_HOST = "http://localhost:11434"

TEMPORAL_TASK_QUEUE = "tether-queue"
TEMPORAL_NAMESPACE = "default"
DAILY_SUMMARY_HOUR = 17
DAILY_SUMMARY_MINUTE = 0


def ensure_directories():
    """Ensure all required directories exist."""
    for directory in [BASE_DIR, RAW_DIR, AUDIO_DIR, SUMMARIES_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
