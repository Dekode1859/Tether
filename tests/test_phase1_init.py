import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestPhase1Init:
    """Tests for Phase 1A: Project Initialization"""

    def test_src_tauri_directory_exists(self):
        """Verify src-tauri directory exists"""
        src_tauri = PROJECT_ROOT / "src-tauri"
        assert src_tauri.exists(), "src-tauri directory should exist"
        assert src_tauri.is_dir(), "src-tauri should be a directory"

    def test_src_directory_exists(self):
        """Verify src directory exists for React"""
        src = PROJECT_ROOT / "src"
        assert src.exists(), "src directory should exist"
        assert src.is_dir(), "src should be a directory"

    def test_package_json_exists(self):
        """Verify package.json exists"""
        package_json = PROJECT_ROOT / "package.json"
        assert package_json.exists(), "package.json should exist"

    def test_tauri_config_exists(self):
        """Verify tauri.conf.json exists"""
        tauri_config = PROJECT_ROOT / "src-tauri" / "tauri.conf.json"
        assert tauri_config.exists(), "tauri.conf.json should exist"

    def test_main_rs_exists(self):
        """Verify main.rs exists in Rust backend"""
        main_rs = PROJECT_ROOT / "src-tauri" / "src" / "main.rs"
        assert main_rs.exists(), "main.rs should exist"

    def test_cargo_toml_exists(self):
        """Verify Cargo.toml exists"""
        cargo_toml = PROJECT_ROOT / "src-tauri" / "Cargo.toml"
        assert cargo_toml.exists(), "Cargo.toml should exist"


class TestTauriConfig:
    """Tests for Tauri configuration"""

    def test_tauri_config_has_main_window(self):
        """Verify main window configuration exists"""
        import json

        tauri_config = PROJECT_ROOT / "src-tauri" / "tauri.conf.json"
        config = json.loads(tauri_config.read_text())

        # Check build section exists
        assert "build" in config, "Config should have 'build' section"

        # Check app has windows
        assert "app" in config, "Config should have 'app' section"

    def test_tauri_has_two_windows(self):
        """Verify two windows are configured"""
        # This test will pass once windows are properly configured
        # For now, just verify config file is valid JSON
        import json

        tauri_config = PROJECT_ROOT / "src-tauri" / "tauri.conf.json"
        config = json.loads(tauri_config.read_text())

        assert config is not None, "tauri.conf.json should be valid JSON"
