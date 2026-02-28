import pytest
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestPortablePython:
    """Tests for portable Python runtime and engine integration"""

    def test_python_runtime_exists(self):
        """Verify python-runtime directory exists"""
        runtime_dir = PROJECT_ROOT / "python-runtime"
        assert runtime_dir.exists(), "python-runtime directory should exist"

    def test_python_executable_in_runtime(self):
        """Verify Python executable exists in runtime"""
        # Check Scripts folder (Windows)
        python_exe = PROJECT_ROOT / "python-runtime" / "Scripts" / "python.exe"

        # Also check root (Unix)
        if not python_exe.exists():
            python_exe = PROJECT_ROOT / "python-runtime" / "python.exe"

        assert python_exe.exists(), "Python executable should exist in runtime"

    def test_engine_runs_help(self):
        """Verify engine module runs with --help"""
        # Find Python executable
        python_exe = PROJECT_ROOT / "python-runtime" / "Scripts" / "python.exe"
        if not python_exe.exists():
            python_exe = PROJECT_ROOT / "python-runtime" / "python.exe"

        # Run engine with --help
        result = subprocess.run(
            [str(python_exe), "-m", "engine", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Engine --help failed: {result.stderr}"
        assert "spool" in result.stdout.lower()
        assert "weave" in result.stdout.lower()
        assert "ask" in result.stdout.lower()

    def test_engine_imports_work(self):
        """Verify engine imports work when called as module"""
        python_exe = PROJECT_ROOT / "python-runtime" / "Scripts" / "python.exe"
        if not python_exe.exists():
            python_exe = PROJECT_ROOT / "python-runtime" / "python.exe"

        # Test imports
        test_code = """
import sys
sys.path.insert(0, '.')
from engine.utils import get_tether_dir, get_vault_dir
print("Imports OK")
"""
        result = subprocess.run(
            [str(python_exe), "-c", test_code],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=30,
        )

        assert result.returncode == 0, f"Import test failed: {result.stderr}"
        assert "Imports OK" in result.stdout


class TestBundledEngine:
    """Tests for bundled engine in release folder"""

    def test_release_folder_has_engine(self):
        """Verify release folder has engine folder"""
        release_dir = PROJECT_ROOT / "src-tauri" / "target" / "release"
        if not release_dir.exists():
            pytest.skip("Release folder not found - build required")

        engine_dir = release_dir / "engine"
        assert engine_dir.exists(), "Engine should be bundled in release"

    def test_release_folder_has_python_runtime(self):
        """Verify release folder has python-runtime"""
        release_dir = PROJECT_ROOT / "src-tauri" / "target" / "release"
        if not release_dir.exists():
            pytest.skip("Release folder not found - build required")

        runtime_dir = release_dir / "python-runtime"
        assert runtime_dir.exists(), "Python runtime should be bundled in release"

    def test_release_python_runs_engine(self):
        """Verify release Python can run engine module"""
        release_dir = PROJECT_ROOT / "src-tauri" / "target" / "release"
        if not release_dir.exists():
            pytest.skip("Release folder not found - build required")

        # Find Python in release
        python_exe = release_dir / "python-runtime" / "Scripts" / "python.exe"
        if not python_exe.exists():
            python_exe = release_dir / "python-runtime" / "python.exe"

        if not python_exe.exists():
            pytest.skip("Python not found in release")

        # Run engine with --help
        result = subprocess.run(
            [str(python_exe), "-m", "engine", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Release engine failed: {result.stderr}"


class TestBuildArtifacts:
    """Tests for final build artifacts"""

    def test_tauri_exe_exists(self):
        """Verify Tauri executable exists"""
        release_dir = PROJECT_ROOT / "src-tauri" / "target" / "release"
        if not release_dir.exists():
            pytest.skip("Release folder not found - build required")

        exe_path = release_dir / "tether.exe"
        assert exe_path.exists(), "tether.exe should exist in release"

    def test_installer_exists(self):
        """Verify installer was created"""
        release_dir = PROJECT_ROOT / "src-tauri" / "target" / "release"
        if not release_dir.exists():
            pytest.skip("Release folder not found - build required")

        # Check for MSI or NSIS installer
        msi_path = release_dir / "bundle" / "msi" / "Tether_0.1.0_x64_en-US.msi"
        nsis_path = release_dir / "bundle" / "nsis" / "Tether_0.1.0_x64-setup.exe"

        has_installer = msi_path.exists() or nsis_path.exists()
        assert has_installer, "At least one installer should exist"
