import json
from pathlib import Path
from typing import Optional

from core import BASE_DIR, ensure_directories

CONFIG_FILE = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "llm_enabled": True,
    "daily_summary_hour": 17,
    "daily_summary_minute": 0,
}


class ConfigManager:
    """Manages application configuration stored in JSON."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self._config = None

    def _ensure_config_exists(self):
        """Ensure config file exists with defaults."""
        if not self.config_path.exists():
            ensure_directories()
            self._config = DEFAULT_CONFIG.copy()
            self.save()

    def load(self) -> dict:
        """Load config from file."""
        self._ensure_config_exists()
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)
        return self._config

    def save(self):
        """Save config to file."""
        ensure_directories()
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2)

    def get(self, key: str, default=None):
        """Get a config value."""
        if self._config is None:
            self.load()
        return self._config.get(key, default)

    def set(self, key: str, value):
        """Set a config value and save."""
        if self._config is None:
            self.load()
        self._config[key] = value
        self.save()

    @property
    def llm_enabled(self) -> bool:
        """Check if LLM summaries are enabled."""
        return self.get("llm_enabled", True)

    @llm_enabled.setter
    def llm_enabled(self, value: bool):
        self.set("llm_enabled", value)

    @property
    def daily_summary_hour(self) -> int:
        """Get daily summary hour."""
        return self.get("daily_summary_hour", 17)

    @property
    def daily_summary_minute(self) -> int:
        """Get daily summary minute."""
        return self.get("daily_summary_minute", 0)


def get_config() -> ConfigManager:
    """Get the global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        _config_manager.load()
    return _config_manager


_config_manager: Optional[ConfigManager] = None
