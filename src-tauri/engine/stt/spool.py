from pathlib import Path
from datetime import datetime
from typing import Optional


def get_vault_dir() -> Path:
    """Get the vault directory."""
    from ..utils import get_tether_dir

    vault_dir = get_tether_dir() / "vault"
    vault_dir.mkdir(exist_ok=True)
    return vault_dir


def get_daily_dir() -> Path:
    """Get the daily notes directory."""
    daily_dir = get_vault_dir() / "Daily"
    daily_dir.mkdir(exist_ok=True)
    return daily_dir


class Spool:
    """Handles appending transcribed text to daily vault files."""

    def __init__(self, daily_dir: Path = None):
        if daily_dir is None:
            daily_dir = get_daily_dir()
        self.daily_dir = daily_dir

    def _get_daily_path(self, date: Optional[datetime] = None) -> Path:
        """Get the daily file path for a given date."""
        if date is None:
            date = datetime.now()
        filename = date.strftime("%Y-%m-%d.md")
        return self.daily_dir / filename

    def append(self, text: str, timestamp: Optional[datetime] = None) -> Path:
        """Append text to today's daily note."""
        if timestamp is None:
            timestamp = datetime.now()

        daily_path = self._get_daily_path(timestamp)

        time_str = timestamp.strftime("%H:%M:%S")
        entry = f"- **[{time_str}]**: {text}\n"

        # Check if file exists and has content
        if daily_path.exists():
            existing = daily_path.read_text(encoding="utf-8")
            # If file is empty or just has frontmatter, add content
            if not existing.strip() or existing.strip() == "---":
                frontmatter = (
                    "---\ndate: " + timestamp.strftime("%Y-%m-%d") + "\n---\n\n"
                )
                daily_path.write_text(frontmatter + entry, encoding="utf-8")
            else:
                with open(daily_path, "a", encoding="utf-8") as f:
                    f.write(entry)
        else:
            frontmatter = "---\ndate: " + timestamp.strftime("%Y-%m-%d") + "\n---\n\n"
            daily_path.write_text(frontmatter + entry, encoding="utf-8")

        return daily_path

    def read_today(self) -> str:
        """Read all content from today's daily note."""
        daily_path = self._get_daily_path()
        if not daily_path.exists():
            return ""
        return daily_path.read_text(encoding="utf-8")

    def read_date(self, date: datetime) -> str:
        """Read all content from a specific date's daily note."""
        daily_path = self._get_daily_path(date)
        if not daily_path.exists():
            return ""
        return daily_path.read_text(encoding="utf-8")
