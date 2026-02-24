from typing import Callable
from core import HOTKEY_DEFAULT


class HotkeyManager:
    """Manages global hotkey registration and callbacks."""

    def __init__(self, hotkey: str = HOTKEY_DEFAULT):
        self.hotkey = hotkey
        self._callback = None
        self._registered = False
        self._keyboard = None

    def _get_keyboard(self):
        """Lazy load keyboard module."""
        if self._keyboard is None:
            import keyboard

            self._keyboard = keyboard
        return self._keyboard

    def register(self, callback: Callable[[], None]):
        """Register a callback to be triggered on hotkey press."""
        self._callback = callback
        keyboard = self._get_keyboard()
        keyboard.add_hotkey(self.hotkey, self._callback)
        self._registered = True

    def unregister(self):
        """Unregister the hotkey."""
        if self._registered:
            keyboard = self._get_keyboard()
            keyboard.remove_hotkey(self.hotkey)
            self._registered = False
            self._callback = None
