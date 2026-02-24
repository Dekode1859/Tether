from .config import (
    BASE_DIR,
    RAW_DIR,
    AUDIO_DIR,
    SUMMARIES_DIR,
    HOTKEY_DEFAULT,
    WHISPER_MODEL,
    OLLAMA_MODEL,
    OLLAMA_HOST,
    DAILY_SUMMARY_HOUR,
    DAILY_SUMMARY_MINUTE,
    ensure_directories,
)
from .config_manager import ConfigManager, get_config, CONFIG_FILE
