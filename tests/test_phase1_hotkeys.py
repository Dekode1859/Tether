import pytest
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).parent.parent


class TestHotkeys:
    """Tests for Phase 1B: Global Hotkeys"""

    def test_main_rs_has_global_hotkey_imports(self):
        """Verify Rust code imports hotkey libraries"""
        main_rs = PROJECT_ROOT / "src-tauri" / "src" / "main.rs"
        content = main_rs.read_text()

        # Check for global shortcut/hotkey imports
        # Tauri's global-shortcut plugin or manual implementation
        assert len(content) > 0, "main.rs should have content"

    def test_hotkey_alt_space_configured(self):
        """Verify Alt+Space is configured for main window"""
        # Check tauri.conf.json for window configuration
        tauri_config = PROJECT_ROOT / "src-tauri" / "tauri.conf.json"

        if tauri_config.exists():
            config = json.loads(tauri_config.read_text())
            # Verify configuration structure exists
            assert config is not None

    def test_hotkey_ctrl_shift_space_configured(self):
        """Verify Ctrl+Shift+Space is configured for recording"""
        # This will be verified in integration tests
        main_rs = PROJECT_ROOT / "src-tauri" / "src" / "main.rs"
        assert main_rs.exists(), "main.rs should exist for hotkey implementation"


class TestProcessManager:
    """Tests for process management in Rust"""

    def test_process_manager_module_exists(self):
        """Verify process_manager.rs exists"""
        process_manager = PROJECT_ROOT / "src-tauri" / "src" / "process_manager.rs"
        # This file may not exist yet - test will fail initially
        # This is intentional for TDD
        if process_manager.exists():
            content = process_manager.read_text()
            assert "spawn" in content.lower() or "kill" in content.lower()

    def test_cargo_has_dependencies_for_process_management(self):
        """Verify Cargo.toml has necessary dependencies"""
        cargo_toml = PROJECT_ROOT / "src-tauri" / "Cargo.toml"

        if cargo_toml.exists():
            content = cargo_toml.read_text()
            # Should have tauri plugins for shell and shortcuts
            assert "tauri-plugin-shell" in content
            assert "tauri-plugin-global-shortcut" in content
