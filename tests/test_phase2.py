import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import os

from app.stt import Transcriber, Spool


class TestTranscriber:
    """Test transcriber functionality."""

    def test_transcriber_init(self):
        transcriber = Transcriber()
        assert transcriber.model_size == "small.en"
        assert transcriber._model is None

    def test_transcriber_custom_model(self):
        transcriber = Transcriber("tiny.en")
        assert transcriber.model_size == "tiny.en"

    def test_transcribe_method_exists(self):
        transcriber = Transcriber()
        assert hasattr(transcriber, "transcribe")
        assert callable(transcriber.transcribe)

    def test_transcribe_async_method_exists(self):
        transcriber = Transcriber()
        assert hasattr(transcriber, "transcribe_async")
        assert callable(transcriber.transcribe_async)


class TestSpool:
    """Test spool functionality."""

    def test_spool_init(self):
        spool = Spool()
        assert spool.raw_dir.name == "raw"

    def test_spool_append(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spool = Spool(Path(tmpdir))
            result = spool.append("Test transcription")
            assert result.exists()
            content = result.read_text()
            assert "Test transcription" in content
            assert "[00:00:00]" in content or "[" in content

    def test_spool_append_with_timestamp(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spool = Spool(Path(tmpdir))
            test_time = datetime(2024, 1, 15, 10, 30, 0)
            spool.append("Test with time", test_time)
            spool_path = spool._get_spool_path(test_time)
            content = spool_path.read_text()
            assert "[2024-01-15 10:30:00]" in content

    def test_spool_read_today_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spool = Spool(Path(tmpdir))
            result = spool.read_today()
            assert result == ""

    def test_spool_read_date(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spool = Spool(Path(tmpdir))
            test_date = datetime(2024, 1, 15)
            spool.append("Test content", test_date)
            result = spool.read_date(test_date)
            assert "Test content" in result

    def test_spool_date_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spool = Spool(Path(tmpdir))
            test_date = datetime(2024, 1, 15, 14, 30, 0)
            spool_path = spool._get_spool_path(test_date)
            assert "2024-01-15-spool.txt" in str(spool_path)
