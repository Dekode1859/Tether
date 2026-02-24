from typing import Optional


class Notifier:
    """Handles OS native notifications using plyer."""

    def __init__(self):
        self._notification = None

    def _get_notification(self):
        """Lazy load plyer notification."""
        if self._notification is None:
            from plyer import notification

            self._notification = notification
        return self._notification

    def notify(self, title: str, message: str, timeout: int = 10):
        """
        Send a desktop notification.

        Args:
            title: Notification title
            message: Notification message
            timeout: Duration to show notification (seconds)
        """
        notifier = self._get_notification()
        notifier.notify(
            title=title,
            message=message,
            app_name="Tether",
            timeout=timeout,
        )

    async def notify_async(self, title: str, message: str, timeout: int = 10):
        """Async wrapper for notify."""
        import asyncio

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.notify, title, message, timeout)
