import logging
from datetime import datetime
from pathlib import Path

from core import ensure_directories
from core.llm_client import LLMClient
from app.stt.spool import Spool
from jobs.notifier import Notifier

logger = logging.getLogger(__name__)


class DailySummarizer:
    """Handles daily summarization of spool content."""

    def __init__(self):
        self.llm = LLMClient()
        self.spool = Spool()
        self.notifier = Notifier()

    def summarize_date(self, date: datetime = None) -> Path:
        """
        Generate and save summary for a specific date.

        Args:
            date: Date to summarize (defaults to today)

        Returns:
            Path to the saved summary file
        """
        if date is None:
            date = datetime.now()

        ensure_directories()

        content = self.spool.read_date(date)
        if not content:
            raise ValueError(f"No content found for date {date.strftime('%Y-%m-%d')}")

        logger.info(f"Generating summary for {date.strftime('%Y-%m-%d')}")

        from core.prompts import (
            get_summary_prompt,
            get_action_items_prompt,
            get_technical_ideas_prompt,
            SUMMARY_SYSTEM_PROMPT,
        )

        journal = self.llm.query(get_summary_prompt(content), SUMMARY_SYSTEM_PROMPT)

        action_items = self.llm.query(
            get_action_items_prompt(content), SUMMARY_SYSTEM_PROMPT
        )

        technical_ideas = self.llm.query(
            get_technical_ideas_prompt(content), SUMMARY_SYSTEM_PROMPT
        )

        summary = {
            "journal": journal,
            "action_items": action_items,
            "technical_ideas": technical_ideas,
        }

        markdown = self._generate_markdown(summary, date)

        from core import SUMMARIES_DIR

        filename = date.strftime("%Y-%m-%d-summary.md")
        filepath = SUMMARIES_DIR / filename
        filepath.write_text(markdown, encoding="utf-8")

        logger.info(f"Summary saved to {filepath}")

        self.notifier.notify(
            "Tether Daily Summary Ready",
            f"Your summary for {date.strftime('%Y-%m-%d')} is ready!",
        )

        return filepath

    def _generate_markdown(self, summary: dict, date: datetime) -> str:
        """Generate markdown from summary dict."""
        md = f"# Daily Summary - {date.strftime('%Y-%m-%d')}\n\n"

        md += "## Journal Entries\n"
        md += f"{summary.get('journal', 'No journal entries.')}\n\n"

        md += "## Action Items\n"
        md += f"{summary.get('action_items', 'No action items.')}\n\n"

        md += "## Technical Ideas\n"
        md += f"{summary.get('technical_ideas', 'No technical ideas.')}\n"

        return md


def run_daily_summary(date: datetime = None):
    """
    Run the daily summary job.

    This is the main entry point for the scheduler.

    Args:
        date: Optional date to summarize (defaults to today)
    """
    summarizer = DailySummarizer()
    return summarizer.summarize_date(date)


def run_specific_date(date_str: str):
    """
    Run summary for a specific date string.

    Args:
        date_str: Date in YYYY-MM-DD format
    """
    date = datetime.strptime(date_str, "%Y-%m-%d")
    return run_daily_summary(date)
