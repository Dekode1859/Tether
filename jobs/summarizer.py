from pathlib import Path
from datetime import datetime
from typing import Optional

from core import SUMMARIES_DIR, ensure_directories
from core.llm_client import LLMClient
from core.prompts import (
    get_summary_prompt,
    get_action_items_prompt,
    get_technical_ideas_prompt,
    SUMMARY_SYSTEM_PROMPT,
)
from app.stt.spool import Spool


class Summarizer:
    """Handles LLM-powered summarization of spool content."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.spool = Spool()

    def summarize(self, content: str) -> dict:
        """
        Generate a full summary from raw content.

        Returns:
            Dictionary with 'journal', 'action_items', 'technical_ideas'
        """
        journal = self.llm.query(get_summary_prompt(content), SUMMARY_SYSTEM_PROMPT)

        action_items = self.llm.query(
            get_action_items_prompt(content), SUMMARY_SYSTEM_PROMPT
        )

        technical_ideas = self.llm.query(
            get_technical_ideas_prompt(content), SUMMARY_SYSTEM_PROMPT
        )

        return {
            "journal": journal,
            "action_items": action_items,
            "technical_ideas": technical_ideas,
        }

    def generate_markdown(self, summary: dict, date: Optional[datetime] = None) -> str:
        """Generate markdown from summary dict."""
        if date is None:
            date = datetime.now()

        md = f"# Daily Summary - {date.strftime('%Y-%m-%d')}\n\n"

        md += "## Journal Entries\n"
        md += f"{summary.get('journal', 'No journal entries.')}\n\n"

        md += "## Action Items\n"
        md += f"{summary.get('action_items', 'No action items.')}\n\n"

        md += "## Technical Ideas\n"
        md += f"{summary.get('technical_ideas', 'No technical ideas.')}\n"

        return md

    def save_summary(self, date: Optional[datetime] = None) -> Path:
        """Generate and save summary for a specific date."""
        if date is None:
            date = datetime.now()

        ensure_directories()

        content = self.spool.read_date(date)
        if not content:
            raise ValueError(f"No content found for date {date.strftime('%Y-%m-%d')}")

        summary = self.summarize(content)
        markdown = self.generate_markdown(summary, date)

        filename = date.strftime("%Y-%m-%d-summary.md")
        filepath = SUMMARIES_DIR / filename
        filepath.write_text(markdown, encoding="utf-8")

        return filepath

    def save_today_summary(self) -> Path:
        """Generate and save today's summary."""
        return self.save_summary(datetime.now())

    async def summarize_async(self, content: str) -> dict:
        """Async wrapper for summarize."""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.summarize, content)
