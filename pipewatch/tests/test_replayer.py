"""Tests for pipewatch.replayer."""

import pytest
from datetime import datetime, timedelta
from typing import List
from unittest.mock import MagicMock

from pipewatch.checker import Alert
from pipewatch.history import HistoryEntry, HistoryStore
from pipewatch.replayer import replay_history, ReplayResult


def make_entry(
    pipeline: str = "pipe_a",
    alerts: List[Alert] = None,
    ts: datetime = None,
) -> HistoryEntry:
    return HistoryEntry(
        pipeline=pipeline,
        alerts=alerts or [],
        timestamp=ts or datetime(2024, 6, 1, 12, 0, 0),
    )


@pytest.fixture
def store(tmp_path):
    s = HistoryStore(path=str(tmp_path / "history.json"))
    return s


def test_replay_empty_store_returns_zero(store):
    result = replay_history(store, handler=lambda p, a: None)
    assert result.replayed == 0
    assert result.errors == 0


def test_replay_calls_handler_for_each_entry(store):
    alert = Alert(pipeline="pipe_a", metric="error_rate", value=0.5, threshold=0.1, severity="critical")
    store.record(make_entry("pipe_a", [alert]))
    store.record(make_entry("pipe_b", []))

    calls = []
    replay_history(store, handler=lambda p, a: calls.append((p, a)))

    assert len(calls) == 2


def test_replay_filter_by_pipeline(store):
    store.record(make_entry("pipe_a"))
    store.record(make_entry("pipe_b"))

    calls = []
    replay_history(store, handler=lambda p, a: calls.append(p), pipeline="pipe_a")

    assert calls == ["pipe_a"]


def test_replay_filter_by_since(store):
    early = datetime(2024, 1, 1)
    late = datetime(2024, 6, 1)
    store.record(make_entry(ts=early))
    store.record(make_entry(ts=late))

    calls = []
    replay_history(
        store,
        handler=lambda p, a: calls.append(p),
        since=datetime(2024, 3, 1),
    )

    assert len(calls) == 1


def test_replay_limit(store):
    for i in range(5):
        store.record(make_entry(f"pipe_{i}"))

    calls = []
    replay_history(store, handler=lambda p, a: calls.append(p), limit=3)

    assert len(calls) == 3


def test_replay_handler_exception_counts_as_error(store):
    store.record(make_entry("pipe_a"))

    def bad_handler(p, a):
        raise RuntimeError("boom")

    result = replay_history(store, handler=bad_handler)
    assert result.errors == 1
    assert result.replayed == 0
    assert any("ERROR" in line for line in result.outputs)


def test_replay_result_summary_string(store):
    store.record(make_entry("pipe_a"))
    result = replay_history(store, handler=lambda p, a: None)
    assert "Replayed" in result.summary
    assert "skipped" in result.summary
