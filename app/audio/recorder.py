import threading
from pathlib import Path
from datetime import datetime

from core import AUDIO_DIR, ensure_directories


class AudioRecorder:
    """Captures audio from microphone and saves to file."""

    def __init__(self, sample_rate=16000, channels=1, dtype="int16"):
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self._is_recording = False
        self._audio_buffer = []
        self._stream = None
        self._lock = threading.Lock()
        self._sd = None

    def _get_sounddevice(self):
        """Lazy load sounddevice."""
        if self._sd is None:
            import sounddevice as sd

            self._sd = sd
        return self._sd

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream."""
        if self._is_recording:
            with self._lock:
                self._audio_buffer.append(indata.copy())

    def start(self):
        """Start recording audio."""
        if self._is_recording:
            return False

        ensure_directories()
        self._audio_buffer = []
        self._is_recording = True

        sd = self._get_sounddevice()
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            callback=self._audio_callback,
        )
        self._stream.start()
        return True

    def stop(self) -> Path | None:
        """Stop recording and save audio to file."""
        if not self._is_recording:
            return None

        self._is_recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._audio_buffer:
            return None

        import numpy as np

        with self._lock:
            audio_data = np.concatenate(self._audio_buffer)

        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        filename = f"{timestamp}.wav"
        filepath = AUDIO_DIR / filename

        import wave

        with wave.open(str(filepath), "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())

        return filepath

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording
