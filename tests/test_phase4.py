import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime
import tempfile

from jobs.notifier import Notifier
from jobs.scheduler import Scheduler, start_scheduler
from jobs.summarize import DailySummarizer, run_daily_summary


class TestNotifier:
    """Test notifier functionality."""

    def test_notifier_init(self):
        notifier = Notifier()
        assert notifier._notification is None

    def test_notify_method_exists(self):
        notifier = Notifier()
        assert hasattr(notifier, "notify")
        assert callable(notifier.notify)

    def test_notify_async_method_exists(self):
        notifier = Notifier()
        assert hasattr(notifier, "notify_async")
        assert callable(notifier.notify_async)

    def test_notify_with_mock(self):
        notifier = Notifier()
        mock_notification = MagicMock()
        notifier._notification = mock_notification

        notifier.notify("Test Title", "Test Message")

        mock_notification.notify.assert_called_once()
        call_kwargs = mock_notification.notify.call_args.kwargs
        assert call_kwargs["title"] == "Test Title"
        assert call_kwargs["message"] == "Test Message"
        assert call_kwargs["app_name"] == "Tether"


class TestScheduler:
    """Test scheduler functionality."""

    def test_scheduler_init_default(self):
        scheduler = Scheduler()
        assert scheduler.hour == 17
        assert scheduler.minute == 0
        assert scheduler._running is False

    def test_scheduler_init_custom_time(self):
        scheduler = Scheduler(hour=9, minute=30)
        assert scheduler.hour == 9
        assert scheduler.minute == 30

    def test_scheduler_can_be_created(self):
        scheduler = Scheduler()
        assert scheduler.hour == 17
        assert scheduler.minute == 0

    def test_scheduler_has_required_methods(self):
        scheduler = Scheduler()
        assert hasattr(scheduler, "start")
        assert hasattr(scheduler, "stop")
        assert hasattr(scheduler, "run_now")
        assert callable(scheduler.start)
        assert callable(scheduler.stop)
        assert callable(scheduler.run_now)


class TestDailySummarizer:
    """Test daily summarizer functionality."""

    def test_daily_summarizer_init(self):
        summarizer = DailySummarizer()
        assert summarizer.llm is not None
        assert summarizer.spool is not None
        assert summarizer.notifier is not None

    def test_run_daily_summary_function_exists(self):
        assert callable(run_daily_summary)

    def test_daily_summarizer_generates_markdown(self):
        summarizer = DailySummarizer()
        summary = {
            "journal": "Test journal entry",
            "action_items": "- Test task",
            "technical_ideas": "- Test idea",
        }
        test_date = datetime(2024, 1, 15)
        md = summarizer._generate_markdown(summary, test_date)
        assert "# Daily Summary - 2024-01-15" in md
        assert "Journal Entries" in md
        assert "Action Items" in md
        assert "Technical Ideas" in md


class TestSchedulerModule:
    """Test scheduler module imports."""

    def test_scheduler_module_exists(self):
        import jobs.scheduler

        assert jobs.scheduler is not None

    def test_start_scheduler_function_exists(self):
        assert callable(start_scheduler)

    def test_schedule_library_lazy_load(self):
        scheduler = Scheduler()
        assert scheduler._schedule is None
