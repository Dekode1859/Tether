from pathlib import Path
from datetime import datetime
from typing import Optional

from core import RAW_DIR, ensure_directories


class Spool:
    """Handles appending transcribed text to daily spool files."""

    def __init__(self, raw_dir: Path = RAW_DIR):
        self.raw_dir = raw_dir

    def _get_spool_path(self, date: Optional[datetime] = None) -> Path:
        """Get the spool file path for a given date."""
        if date is None:
            date = datetime.now()
        filename = date.strftime("%Y-%m-%d-spool.txt")
        return self.raw_dir / filename

    def append(self, text: str, timestamp: Optional[datetime] = None) -> Path:
        """
        Append text to today's spool file.

        Args:
            text: The transcribed text to append
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Path to the spool file
        """
        if timestamp is None:
            timestamp = datetime.now()

        ensure_directories()
        spool_path = self._get_spool_path(timestamp)

        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{time_str}] {text}\n"

        with open(spool_path, "a", encoding="utf-8") as f:
            f.write(entry)

        return spool_path

    def read_today(self) -> str:
        """Read all content from today's spool file."""
        spool_path = self._get_spool_path()
        if not spool_path.exists():
            return ""
        return spool_path.read_text(encoding="utf-8")

    def read_date(self, date: datetime) -> str:
        """Read all content from a specific date's spool file."""
        spool_path = self._get_spool_path(date)
        if not spool_path.exists():
            return ""
        return spool_path.read_text(encoding="utf-8")
