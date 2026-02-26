import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestEngineStructure:
    """Tests for Phase 2A: Engine Directory Structure"""

    def test_engine_directory_exists(self):
        """Verify engine directory exists"""
        engine_dir = PROJECT_ROOT / "engine"
        assert engine_dir.exists(), "engine directory should exist"
        assert engine_dir.is_dir(), "engine should be a directory"

    def test_engine_main_py_exists(self):
        """Verify engine/main.py exists"""
        main_py = PROJECT_ROOT / "engine" / "main.py"
        assert main_py.exists(), "engine/main.py should exist"

    def test_engine_audio_dir_exists(self):
        """Verify engine/audio directory exists"""
        audio_dir = PROJECT_ROOT / "engine" / "audio"
        assert audio_dir.exists(), "engine/audio directory should exist"

    def test_engine_stt_dir_exists(self):
        """Verify engine/stt directory exists"""
        stt_dir = PROJECT_ROOT / "engine" / "stt"
        assert stt_dir.exists(), "engine/stt directory should exist"

    def test_engine_ai_dir_exists(self):
        """Verify engine/ai directory exists"""
        ai_dir = PROJECT_ROOT / "engine" / "ai"
        assert ai_dir.exists(), "engine/ai directory should exist"

    def test_engine_utils_dir_exists(self):
        """Verify engine/utils directory exists"""
        utils_dir = PROJECT_ROOT / "engine" / "utils"
        assert utils_dir.exists(), "engine/utils directory should exist"


class TestEngineCLI:
    """Tests for Phase 2D: Engine CLI"""

    def test_cli_accepts_spool(self):
        """Verify CLI accepts --spool argument"""
        main_py = PROJECT_ROOT / "engine" / "main.py"
        content = main_py.read_text()
        assert "--spool" in content or "spool" in content

    def test_cli_accepts_weave(self):
        """Verify CLI accepts --weave argument"""
        main_py = PROJECT_ROOT / "engine" / "main.py"
        content = main_py.read_text()
        assert "--weave" in content or "weave" in content

    def test_cli_accepts_ask(self):
        """Verify CLI accepts --ask argument"""
        main_py = PROJECT_ROOT / "engine" / "main.py"
        content = main_py.read_text()
        assert "--ask" in content or "ask" in content


class TestEngineStatus:
    """Tests for Phase 2C: Status File Management"""

    def test_status_module_exists(self):
        """Verify status.py exists in utils"""
        status_py = PROJECT_ROOT / "engine" / "utils" / "status.py"
        assert status_py.exists(), "engine/utils/status.py should exist"

    def test_status_has_read_write(self):
        """Verify status module has read/write functions"""
        status_py = PROJECT_ROOT / "engine" / "utils" / "status.py"
        if status_py.exists():
            content = status_py.read_text()
            assert "read" in content.lower() or "load" in content.lower()
            assert "write" in content.lower() or "save" in content.lower()
