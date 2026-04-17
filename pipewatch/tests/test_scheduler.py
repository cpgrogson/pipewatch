"""Tests for pipewatch.scheduler."""

import pytest
from unittest.mock import MagicMock, patch
from pipewatch.scheduler import ScheduleConfig, CheckScheduler


@pytest.fixture
def schedule_config():
    return ScheduleConfig(interval_seconds=5, max_runs=3)


def test_schedule_config_defaults():
    cfg = ScheduleConfig()
    assert cfg.interval_seconds == 60
    assert cfg.max_runs is None


def test_schedule_config_custom():
    cfg = ScheduleConfig(interval_seconds=30, max_runs=5)
    assert cfg.interval_seconds == 30
    assert cfg.max_runs == 5


def test_scheduler_runs_exact_max_runs(schedule_config):
    mock_fn = MagicMock()
    scheduler = CheckScheduler(schedule_config, mock_fn)

    with patch("time.sleep"):
        scheduler.start()

    assert mock_fn.call_count == 3
    assert scheduler.runs_completed == 3


def test_scheduler_records_last_run(schedule_config):
    mock_fn = MagicMock()
    scheduler = CheckScheduler(schedule_config, mock_fn)

    with patch("time.sleep"):
        scheduler.start()

    assert scheduler.last_run is not None


def test_scheduler_continues_on_check_error(schedule_config):
    def failing_fn():
        raise RuntimeError("pipeline error")

    scheduler = CheckScheduler(schedule_config, failing_fn)

    with patch("time.sleep"):
        scheduler.start()  # should not raise

    assert scheduler.runs_completed == 3


def test_scheduler_stop_sets_flag():
    cfg = ScheduleConfig(interval_seconds=1, max_runs=None)
    call_count = 0

    def check_fn():
        nonlocal call_count
        call_count += 1
        scheduler.stop()

    scheduler = CheckScheduler(cfg, check_fn)

    with patch("time.sleep"):
        scheduler.start()

    assert call_count == 1
    assert not scheduler._running
