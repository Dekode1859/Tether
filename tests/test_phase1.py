import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import threading
import time

from app.audio import AudioRecorder
from app.tray import TrayIcon, TrayState, HotkeyManager


class TestAudioRecorder:
    """Test audio recorder functionality."""

    def test_recorder_init(self):
        recorder = AudioRecorder()
        assert recorder.sample_rate == 16000
        assert recorder.channels == 1
        assert not recorder.is_recording()

    def test_stop_without_start(self):
        recorder = AudioRecorder()
        result = recorder.stop()
        assert result is None
        assert not recorder.is_recording()

    def test_start_sets_recording_state(self):
        recorder = AudioRecorder()
        with patch.object(recorder, "_get_sounddevice") as mock_get_sd:
            mock_sd = MagicMock()
            mock_get_sd.return_value = mock_sd
            result = recorder.start()
            assert result is True
            assert recorder.is_recording()


class TestHotkeyManager:
    """Test hotkey manager functionality."""

    def test_register(self):
        callback = Mock()
        manager = HotkeyManager()
        with patch.object(manager, "_get_keyboard") as mock_get_kb:
            mock_kb = MagicMock()
            mock_get_kb.return_value = mock_kb
            manager.register(callback)
            mock_kb.add_hotkey.assert_called_once()

    def test_unregister(self):
        callback = Mock()
        manager = HotkeyManager()
        with patch.object(manager, "_get_keyboard") as mock_get_kb:
            mock_kb = MagicMock()
            mock_get_kb.return_value = mock_kb
            manager.register(callback)
            manager.unregister()
            mock_kb.remove_hotkey.assert_called_once()


class TestTrayIcon:
    """Test tray icon functionality."""

    def test_tray_init(self):
        tray = TrayIcon()
        assert tray.state == TrayState.IDLE
        assert not tray.recorder.is_recording()

    def test_toggle_from_idle(self):
        with patch.object(AudioRecorder, "start", return_value=True):
            with patch.object(AudioRecorder, "stop", return_value=None):
                tray = TrayIcon()
                tray.toggle_recording()
                assert tray.state == TrayState.RECORDING

    def test_toggle_from_recording(self):
        with patch.object(AudioRecorder, "start", return_value=True):
            with patch.object(AudioRecorder, "stop", return_value=None):
                tray = TrayIcon()
                tray.recorder._is_recording = True
                tray.toggle_recording()
                assert tray.state == TrayState.IDLE


class TestStorage:
    """Test storage layer."""

    def test_ensure_directories(self):
        from core import BASE_DIR, RAW_DIR, AUDIO_DIR, SUMMARIES_DIR
        from core.config import ensure_directories

        ensure_directories()
        assert BASE_DIR.exists()
        assert RAW_DIR.exists()
        assert AUDIO_DIR.exists()
        assert SUMMARIES_DIR.exists()
