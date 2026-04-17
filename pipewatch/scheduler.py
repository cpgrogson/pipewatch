"""Scheduler for periodic pipeline checks."""

import time
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class ScheduleConfig:
    def __init__(self, interval_seconds: int = 60, max_runs: Optional[int] = None):
        self.interval_seconds = interval_seconds
        self.max_runs = max_runs


class CheckScheduler:
    def __init__(self, config: ScheduleConfig, check_fn: Callable[[], None]):
        self.config = config
        self.check_fn = check_fn
        self._running = False
        self.runs_completed = 0
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None

    def start(self) -> None:
        self._running = True
        logger.info(
            "Scheduler started: interval=%ds, max_runs=%s",
            self.config.interval_seconds,
            self.config.max_runs,
        )
        while self._running:
            self._tick()
            if self.config.max_runs and self.runs_completed >= self.config.max_runs:
                logger.info("Reached max_runs=%d, stopping.", self.config.max_runs)
                break
            self.next_run = datetime.utcnow() + timedelta(seconds=self.config.interval_seconds)
            logger.debug("Next run scheduled at %s", self.next_run.isoformat())
            time.sleep(self.config.interval_seconds)

    def _tick(self) -> None:
        self.last_run = datetime.utcnow()
        logger.info("Running check at %s", self.last_run.isoformat())
        try:
            self.check_fn()
        except Exception as exc:
            logger.error("Check function raised an error: %s", exc)
        self.runs_completed += 1

    def stop(self) -> None:
        self._running = False
        logger.info("Scheduler stopped after %d run(s).", self.runs_completed)
