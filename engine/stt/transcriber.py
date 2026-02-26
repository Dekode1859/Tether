import sys
from pathlib import Path
from typing import Optional


def get_model_path():
    """Get the path to the bundled Whisper model or use default."""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
        model_path = Path(base_path) / "models"
        if model_path.exists():
            return str(model_path)
    return "small.en"


class Transcriber:
    """Handles speech-to-text transcription using faster-whisper."""

    def __init__(self, model_size: str = None):
        if model_size is None:
            model_size = get_model_path()
        self.model_size = model_size
        self._model = None

    def _get_model(self):
        """Lazy load the Whisper model."""
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size, device="cpu", compute_type="int8"
            )
        return self._model

    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file to text."""
        model = self._get_model()
        segments, info = model.transcribe(audio_path, language="en")

        text_parts = []
        for segment in segments:
            text_parts.append(segment.text)

        return " ".join(text_parts).strip()

    async def transcribe_async(self, audio_path: str) -> str:
        """Async wrapper for transcribe."""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.transcribe, audio_path)
