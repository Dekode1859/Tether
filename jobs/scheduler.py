import threading
import time
import logging
from datetime import datetime
from typing import Optional

from core import DAILY_SUMMARY_HOUR, DAILY_SUMMARY_MINUTE
from jobs.summarize import run_daily_summary

logger = logging.getLogger(__name__)


class Scheduler:
    """Lightweight scheduler using the schedule library running in a daemon thread."""

    def __init__(
        self, hour: int = DAILY_SUMMARY_HOUR, minute: int = DAILY_SUMMARY_MINUTE
    ):
        self.hour = hour
        self.minute = minute
        self._running = False
        self._thread = None
        self._schedule = None

    def _get_schedule(self):
        """Lazy load schedule library."""
        if self._schedule is None:
            import schedule

            self._schedule = schedule
        return self._schedule

    def _setup_jobs(self):
        """Configure scheduled jobs."""
        schedule = self._get_schedule()
        schedule.clear()

        schedule.every().day.at(f"{self.hour:02d}:{self.minute:02d}").do(
            self._run_summary_job
        )

        logger.info(
            f"Scheduler configured to run daily at {self.hour:02d}:{self.minute:02d}"
        )

    def _run_summary_job(self):
        """Run the daily summary job with retry logic."""
        logger.info("Starting daily summary job...")

        max_retries = 3
        retry_delay_minutes = 30

        last_error = None
        for attempt in range(max_retries):
            try:
                run_daily_summary()
                logger.info("Daily summary completed successfully")
                return
            except Exception as e:
                last_error = e
                logger.warning(f"Summary attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay_minutes} minutes...")
                    time.sleep(retry_delay_minutes * 60)

        logger.error(f"All retry attempts failed: {last_error}")

        try:
            from jobs.notifier import Notifier

            notifier = Notifier()
            notifier.notify(
                "Tether Error",
                f"Failed to generate daily summary after {max_retries} attempts",
            )
        except Exception as notify_error:
            logger.error(f"Failed to send error notification: {notify_error}")

    def start(self):
        """Start the scheduler in a daemon thread."""
        if self._running:
            return

        self._setup_jobs()
        self._running = True

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._schedule:
            self._schedule.clear()
        logger.info("Scheduler stopped")

    def _run_loop(self):
        """Main scheduler loop."""
        schedule = self._get_schedule()
        while self._running:
            schedule.run_pending()
            time.sleep(1)

    def run_now(self):
        """Trigger the summary job immediately."""
        self._run_summary_job()


def start_scheduler(
    hour: int = DAILY_SUMMARY_HOUR, minute: int = DAILY_SUMMARY_MINUTE
) -> Scheduler:
    """
    Start the background scheduler.

    Args:
        hour: Hour to run daily summary (default from config)
        minute: Minute to run daily summary (default from config)

    Returns:
        Scheduler instance
    """
    scheduler = Scheduler(hour=hour, minute=minute)
    scheduler.start()
    return scheduler
