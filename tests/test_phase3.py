import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime
import tempfile

from core.llm_client import LLMClient
from core.prompts import (
    get_summary_prompt,
    get_action_items_prompt,
    get_technical_ideas_prompt,
    SUMMARY_SYSTEM_PROMPT,
)
from jobs import Summarizer


class TestLLMClient:
    """Test LLM client functionality."""

    def test_llm_client_init(self):
        client = LLMClient()
        assert client.model == "llama3"
        assert "localhost" in client.host

    def test_llm_client_custom_params(self):
        client = LLMClient(host="http://custom:1234", model="mistral")
        assert client.model == "mistral"
        assert client.host == "http://custom:1234"

    def test_get_client(self):
        client = LLMClient()
        http_client = client._get_client()
        assert http_client is not None


class TestPrompts:
    """Test prompt generation."""

    def test_get_summary_prompt(self):
        prompt = get_summary_prompt("test content")
        assert "test content" in prompt
        assert "Journal Entries" in prompt
        assert "Action Items" in prompt

    def test_get_action_items_prompt(self):
        prompt = get_action_items_prompt("buy milk")
        assert "buy milk" in prompt

    def test_get_technical_ideas_prompt(self):
        prompt = get_technical_ideas_prompt("use Python")
        assert "use Python" in prompt

    def test_system_prompt_exists(self):
        assert len(SUMMARY_SYSTEM_PROMPT) > 0


class TestSummarizer:
    """Test summarizer functionality."""

    def test_summarizer_init(self):
        summarizer = Summarizer()
        assert summarizer.llm is not None
        assert summarizer.spool is not None

    def test_summarizer_with_custom_client(self):
        mock_client = MagicMock()
        summarizer = Summarizer(llm_client=mock_client)
        assert summarizer.llm is mock_client

    def test_generate_markdown(self):
        summarizer = Summarizer()
        summary = {
            "journal": "Today I worked on the project",
            "action_items": "- Finish testing",
            "technical_ideas": "- Use async/await",
        }
        md = summarizer.generate_markdown(summary)
        assert "# Daily Summary" in md
        assert "Journal Entries" in md
        assert "Action Items" in md
        assert "Technical Ideas" in md
        assert "Today I worked on the project" in md

    def test_generate_markdown_with_date(self):
        summarizer = Summarizer()
        test_date = datetime(2024, 1, 15)
        summary = {"journal": "Test", "action_items": "None", "technical_ideas": "None"}
        md = summarizer.generate_markdown(summary, test_date)
        assert "2024-01-15" in md

    def test_save_summary_no_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spool_path = Path(tmpdir) / "raw" / "2024-01-15-spool.txt"
            spool_path.parent.mkdir(parents=True)
            spool_path.write_text("")

            summarizer = Summarizer()
            summarizer.spool.raw_dir = Path(tmpdir) / "raw"

            with pytest.raises(ValueError):
                summarizer.save_summary(datetime(2024, 1, 15))
