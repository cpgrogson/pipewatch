"""Integration tests for replayer working with real HistoryStore data."""

import pytest
from datetime import datetime
from typing import List

from pipewatch.checker import Alert
from pipewatch.history import HistoryStore, HistoryEntry
from pipewatch.replayer import replay_history
from pipewatch.notifier import LogNotifier


def _make_alert(pipeline: str, metric: str = "error_rate") -> Alert:
    return Alert(
        pipeline=pipeline,
        metric=metric,
        value=0.5,
        threshold=0.1,
        severity="critical",
    )


@pytest.fixture
def populated_store(tmp_path):
    store = HistoryStore(path=str(tmp_path / "history.json"))
    store.record(
        HistoryEntry(
            pipeline="alpha",
            alerts=[_make_alert("alpha")],
            timestamp=datetime(2024, 5, 1),
        )
    )
    store.record(
        HistoryEntry(
            pipeline="beta",
            alerts=[_make_alert("beta", "duration"), _make_alert("beta", "row_count")],
            timestamp=datetime(2024, 5, 2),
        )
    )
    store.record(
        HistoryEntry(
            pipeline="alpha",
            alerts=[],
            timestamp=datetime(2024, 5, 3),
        )
    )
    return store


def test_all_entries_replayed(populated_store):
    seen = []
    replay_history(populated_store, handler=lambda p, a: seen.append(p))
    assert len(seen) == 3


def test_alerts_passed_correctly_to_handler(populated_store):
    collected: List[Alert] = []

    def capture(pipeline: str, alerts: List[Alert]):
        collected.extend(alerts)

    replay_history(populated_store, handler=capture)
    assert len(collected) == 3  # 1 + 2 + 0


def test_replay_with_log_notifier_does_not_raise(populated_store, capsys):
    notifier = LogNotifier()

    def handler(pipeline: str, alerts: List[Alert]):
        notifier.send(alerts)

    result = replay_history(populated_store, handler=handler)
    assert result.errors == 0
    assert result.replayed == 3


def test_replay_since_filters_correctly(populated_store):
    seen = []
    replay_history(
        populated_store,
        handler=lambda p, a: seen.append(p),
        since=datetime(2024, 5, 2),
    )
    assert "alpha" not in seen or seen.count("alpha") == 1
    assert len(seen) == 2
