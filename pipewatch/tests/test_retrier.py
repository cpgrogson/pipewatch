"""Tests for pipewatch.retrier."""
import time
from pathlib import Path

import pytest

from pipewatch.checker import Alert
from pipewatch.retrier import RetryEntry, RetryStore, DEFAULT_MAX_ATTEMPTS


@pytest.fixture
def alert() -> Alert:
    return Alert(pipeline="orders", metric="error_rate", value=0.15, threshold=0.05, severity="critical")


@pytest.fixture
def store(tmp_path: Path) -> RetryStore:
    return RetryStore(path=tmp_path / "retries.json")


def test_enqueue_adds_entry(store: RetryStore, alert: Alert) -> None:
    store.enqueue(alert)
    assert len(store.all()) == 1


def test_entry_from_alert_fields(alert: Alert) -> None:
    entry = RetryEntry.from_alert(alert)
    assert entry.pipeline == "orders"
    assert entry.metric == "error_rate"
    assert entry.severity == "critical"
    assert entry.attempts == 0
    assert entry.max_attempts == DEFAULT_MAX_ATTEMPTS


def test_new_entry_is_immediately_ready(store: RetryStore, alert: Alert) -> None:
    store.enqueue(alert)
    assert len(store.due()) == 1


def test_mark_attempted_increments(store: RetryStore, alert: Alert) -> None:
    store.enqueue(alert)
    entry = store.due()[0]
    store.mark_attempted(entry, backoff=1)
    # after first attempt, next_retry_at is in the future
    assert store.due() == []


def test_exhausted_entry_removed(store: RetryStore, alert: Alert) -> None:
    store.enqueue(alert, max_attempts=1)
    entry = store.due()[0]
    store.mark_attempted(entry, backoff=0)
    assert store.all() == []


def test_clear_removes_all(store: RetryStore, alert: Alert) -> None:
    store.enqueue(alert)
    store.enqueue(alert)
    store.clear()
    assert store.all() == []


def test_persists_to_disk(tmp_path: Path, alert: Alert) -> None:
    path = tmp_path / "retries.json"
    s1 = RetryStore(path=path)
    s1.enqueue(alert)
    s2 = RetryStore(path=path)
    assert len(s2.all()) == 1


def test_is_exhausted_flag() -> None:
    e = RetryEntry(pipeline="p", metric="m", severity="warning", message="msg", attempts=3, max_attempts=3)
    assert e.is_exhausted()


def test_round_trip_dict() -> None:
    e = RetryEntry(pipeline="p", metric="m", severity="warning", message="msg", attempts=1, max_attempts=2)
    restored = RetryEntry.from_dict(e.to_dict())
    assert restored.pipeline == e.pipeline
    assert restored.attempts == e.attempts
    assert restored.max_attempts == e.max_attempts
