import threading
from pathlib import Path
from enum import Enum
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    import pystray
    from PIL import Image

from app.audio import AudioRecorder
from app.tray.hotkey_manager import HotkeyManager
from core import get_config


class TrayState(Enum):
    """Tray icon states."""

    IDLE = "idle"
    RECORDING = "recording"


class TrayIcon:
    """System tray icon with recording functionality and settings."""

    def __init__(self, on_audio_ready: Callable[[str], None] = None):
        self.on_audio_ready = on_audio_ready
        self.state = TrayState.IDLE
        self.recorder = AudioRecorder()
        self.hotkey = HotkeyManager()
        self.config = get_config()
        self._icon = None
        self._thread = None
        self._pystray = None

    def _get_pystray(self):
        """Lazy load pystray."""
        if self._pystray is None:
            import pystray

            self._pystray = pystray
        return self._pystray

    def _create_icon_image(self, state: TrayState) -> "Image":
        """Create icon image based on state."""
        from PIL import Image, ImageDraw

        size = (64, 64)
        image = Image.new("RGB", size, "white")
        draw = ImageDraw.Draw(image)

        if state == TrayState.IDLE:
            color = "gray"
        else:
            color = "red"

        draw.ellipse([8, 8, 56, 56], fill=color, outline="black", width=2)
        return image

    def _on_toggle(self, icon, item):
        """Handle menu toggle click."""
        self.toggle_recording()

    def _on_llm_toggle(self, icon, item):
        """Handle LLM toggle click."""
        current = self.config.llm_enabled
        self.config.llm_enabled = not current
        self._update_menu()

    def _on_exit(self, icon, item):
        """Handle exit click."""
        self.stop()
        icon.stop()

    def toggle_recording(self):
        """Toggle recording state."""
        if self.recorder.is_recording():
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Start audio recording."""
        if self.recorder.start():
            self.state = TrayState.RECORDING
            self._update_icon()

    def _stop_recording(self):
        """Stop audio recording and process the audio."""
        filepath = self.recorder.stop()
        self.state = TrayState.IDLE
        self._update_icon()

        if filepath and self.on_audio_ready:
            self.on_audio_ready(str(filepath))

    def _update_icon(self):
        """Update tray icon appearance."""
        if self._icon:
            self._icon.icon = self._create_icon_image(self.state)
            self._update_menu()

    def _update_menu(self):
        """Update the menu to reflect current state."""
        if self._icon:
            self._icon.menu = self._setup_menu()

    def _setup_menu(self):
        """Setup tray menu with settings."""
        pystray = self._get_pystray()
        state_text = (
            "Stop Recording" if self.state == TrayState.RECORDING else "Start Recording"
        )

        llm_enabled = self.config.llm_enabled

        menu = pystray.Menu(
            pystray.MenuItem(state_text, self._on_toggle),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Enable LLM Summaries",
                self._on_llm_toggle,
                checked=lambda item: llm_enabled,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._on_exit),
        )
        return menu

    def run(self):
        """Run the tray icon."""
        self.hotkey.register(self.toggle_recording)

        pystray = self._get_pystray()
        self._icon = pystray.Icon(
            "tether",
            self._create_icon_image(self.state),
            "Tether - Thought Capture",
            self._setup_menu(),
        )

        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the tray icon and cleanup."""
        self.hotkey.unregister()
        if self.recorder.is_recording():
            self.recorder.stop()
        if self._icon:
            self._icon.stop()
