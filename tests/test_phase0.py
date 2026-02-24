import pytest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent


class TestProjectStructure:
    """Verify project directory structure exists."""

    def test_app_directory_exists(self):
        assert (PROJECT_ROOT / "app").exists()
        assert (PROJECT_ROOT / "app" / "tray").exists()
        assert (PROJECT_ROOT / "app" / "audio").exists()
        assert (PROJECT_ROOT / "app" / "stt").exists()

    def test_jobs_directory_exists(self):
        assert (PROJECT_ROOT / "jobs").exists()

    def test_core_directory_exists(self):
        assert (PROJECT_ROOT / "core").exists()
        assert (PROJECT_ROOT / "core" / "config.py").exists()

    def test_scripts_directory_exists(self):
        assert (PROJECT_ROOT / "scripts").exists()

    def test_tests_directory_exists(self):
        assert (PROJECT_ROOT / "tests").exists()


class TestCoreImports:
    """Verify core module can be imported."""

    def test_config_import(self):
        from core import config

        assert hasattr(config, "BASE_DIR")
        assert hasattr(config, "RAW_DIR")
        assert hasattr(config, "AUDIO_DIR")
        assert hasattr(config, "SUMMARIES_DIR")
        assert hasattr(config, "ensure_directories")

    def test_config_values(self):
        from core.config import (
            HOTKEY_DEFAULT,
            WHISPER_MODEL,
            OLLAMA_MODEL,
            OLLAMA_HOST,
            DAILY_SUMMARY_HOUR,
            DAILY_SUMMARY_MINUTE,
        )

        assert HOTKEY_DEFAULT == "ctrl+shift+space"
        assert WHISPER_MODEL == "small.en"
        assert OLLAMA_MODEL == "llama3"
        assert "localhost" in OLLAMA_HOST
        assert DAILY_SUMMARY_HOUR == 17
        assert DAILY_SUMMARY_MINUTE == 0


class TestPythonVersion:
    """Verify Python version meets requirements."""

    def test_python_version(self):
        assert sys.version_info >= (3, 11)
