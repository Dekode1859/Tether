import pytest
import subprocess
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestEngineCheckMic:
    """Tests for engine --check-mic command"""

    def test_check_mic_command_exists(self):
        """Verify --check-mic argument is accepted"""
        result = subprocess.run(
            ["python", "-m", "engine", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert "--check-mic" in result.stdout

    def test_check_mic_returns_json(self):
        """Verify --check-mic returns valid JSON"""
        result = subprocess.run(
            ["python", "-m", "engine", "--check-mic"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0

        # Should be valid JSON
        data = json.loads(result.stdout)

        # Should have expected fields
        assert "available" in data
        assert "devices" in data
        assert "error" in data
        assert isinstance(data["available"], bool)
        assert isinstance(data["devices"], list)

    def test_check_mic_returns_devices(self):
        """Verify --check-mic returns device information"""
        result = subprocess.run(
            ["python", "-m", "engine", "--check-mic"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        data = json.loads(result.stdout)

        # Should have devices (or none available)
        assert "devices" in data
        assert isinstance(data["devices"], list)


class TestEngineCheckOllama:
    """Tests for engine --check-ollama command"""

    def test_check_ollama_command_exists(self):
        """Verify --check-ollama argument is accepted"""
        result = subprocess.run(
            ["python", "-m", "engine", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert "--check-ollama" in result.stdout

    def test_check_ollama_returns_json(self):
        """Verify --check-ollama returns valid JSON"""
        result = subprocess.run(
            ["python", "-m", "engine", "--check-ollama"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0

        # Should be valid JSON
        data = json.loads(result.stdout)

        # Should have expected fields
        assert "status" in data
        assert "model" in data
        assert data["status"] in ["available", "not_installed", "not_running"]
        assert data["model"] == "granite4:3b"

    def test_check_ollama_returns_not_running(self):
        """Verify --check-ollama returns not_running when Ollama not running"""
        result = subprocess.run(
            ["python", "-m", "engine", "--check-ollama"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        data = json.loads(result.stdout)

        # Status should be one of the expected values
        assert data["status"] in ["available", "not_installed", "not_running"]


class TestEngineInstallOllama:
    """Tests for engine --install-ollama command"""

    def test_install_ollama_command_exists(self):
        """Verify --install-ollama argument is accepted"""
        result = subprocess.run(
            ["python", "-m", "engine", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert "--install-ollama" in result.stdout


class TestEngineModel:
    """Tests for engine model configuration"""

    def test_default_model_is_granite(self):
        """Verify default model is granite4:3b"""
        result = subprocess.run(
            ["python", "-m", "engine", "--check-ollama"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        data = json.loads(result.stdout)

        # Should request granite4:3b
        assert data.get("model") == "granite4:3b"


class TestRustCommands:
    """Tests for Rust command registration"""

    def test_check_mic_command_registered(self):
        """Verify check_mic is in Rust code"""
        lib_rs = PROJECT_ROOT / "src-tauri" / "src" / "lib.rs"
        content = lib_rs.read_text()

        assert "check_mic" in content

    def test_check_ollama_command_registered(self):
        """Verify check_ollama is in Rust code"""
        lib_rs = PROJECT_ROOT / "src-tauri" / "src" / "lib.rs"
        content = lib_rs.read_text()

        assert "check_ollama" in content

    def test_install_ollama_command_registered(self):
        """Verify install_ollama is in Rust code"""
        lib_rs = PROJECT_ROOT / "src-tauri" / "src" / "lib.rs"
        content = lib_rs.read_text()

        assert "install_ollama" in content


class TestUIComponents:
    """Tests for UI components"""

    def test_command_palette_has_install_ollama(self):
        """Verify UI has Install Ollama command"""
        tsx = PROJECT_ROOT / "src" / "components" / "CommandPalette.tsx"
        content = tsx.read_text()

        assert "Install Ollama" in content
        assert "handleInstallOllama" in content

    def test_command_palette_checks_ollama_before_weave(self):
        """Verify weave checks Ollama status first"""
        tsx = PROJECT_ROOT / "src" / "components" / "CommandPalette.tsx"
        content = tsx.read_text()

        # Should call check_ollama before run_weave
        assert "check_ollama" in content
        assert content.index("check_ollama") < content.index("run_weave")
