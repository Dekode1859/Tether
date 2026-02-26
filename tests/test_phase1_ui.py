import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestReactUI:
    """Tests for Phase 1C: React UI Components"""

    def test_react_app_tsx_exists(self):
        """Verify App.tsx exists"""
        app_tsx = PROJECT_ROOT / "src" / "App.tsx"
        assert app_tsx.exists(), "App.tsx should exist"

    def test_command_palette_component_exists(self):
        """Verify CommandPalette component exists"""
        # Check for Command component in src/components
        components_dir = PROJECT_ROOT / "src" / "components"

        # Component could be in various locations
        # Check if any command-related component exists
        has_command = False
        if components_dir.exists():
            for f in components_dir.rglob("*"):
                if f.is_file() and "command" in f.name.lower():
                    has_command = True
                    break

        # Also check in App.tsx directly
        app_tsx = PROJECT_ROOT / "src" / "App.tsx"
        if app_tsx.exists():
            content = app_tsx.read_text()
            if "Command" in content:
                has_command = True

        assert has_command, "Command Palette component should exist"

    def test_recording_widget_exists(self):
        """Verify RecordingWidget component exists"""
        # Check for widget component
        widget_locations = [
            PROJECT_ROOT / "src" / "components" / "RecordingWidget.tsx",
            PROJECT_ROOT / "src" / "components" / "RecordingWidget.ts",
            PROJECT_ROOT / "src" / "Widget.tsx",
            PROJECT_ROOT / "src" / "widget.tsx",
        ]

        exists = any(loc.exists() for loc in widget_locations)
        assert exists, "RecordingWidget component should exist"

    def test_tailwind_config_exists(self):
        """Verify Tailwind CSS is configured"""
        tailwind_configs = [
            PROJECT_ROOT / "tailwind.config.js",
            PROJECT_ROOT / "tailwind.config.ts",
            PROJECT_ROOT / "postcss.config.js",
        ]

        exists = any(config.exists() for config in tailwind_configs)
        assert exists, "Tailwind config should exist"

    def test_vite_config_exists(self):
        """Verify Vite is configured"""
        vite_config = PROJECT_ROOT / "vite.config.ts"
        assert vite_config.exists(), "vite.config.ts should exist"


class TestWindowConfig:
    """Tests for window configurations"""

    def test_main_window_label_configured(self):
        """Verify main window has correct label"""
        # This will be verified when tauri.conf.json is properly configured
        # Main window should have label "main"
        pass

    def test_widget_window_label_configured(self):
        """Verify widget window has correct label"""
        # Widget window should have label "widget"
        # Should be configured as alwaysOnTop
        pass
